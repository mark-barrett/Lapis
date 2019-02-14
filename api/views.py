import base64
import json

from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

import MySQLdb as db

# The main view that handles Private API requests
from api.models import APIRequest, APIKey
from core.models import Resource, ResourceParameter, ResourceHeader, ResourceDataSourceColumn, DatabaseColumn, Database


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class RequestHandlerPrivate(View):

    # First handle GET requests
    def get(self, request):
        # The first thing we need to do is check to see if the header information has been sent for authorisation etc.
        if 'HTTP_AUTHORIZATION' in request.META:
            # Access GET params: print(request.GET)
            # The key was provided so check it. First we need to base64 decode the key.
            # Extract the key from the string. Base64decode, remove the last colon, and decode to utf-8 rather than bytes
            api_key = base64.b64decode(request.META['HTTP_AUTHORIZATION'].split('Basic ',1)[1])[:-1].decode('utf-8')

            # Look up API key
            try:
                api_key = APIKey.objects.get(key=api_key)

                # API Key is found. No check for a resource.
                if 'HTTP_RESTBROKER_RESOURCE' in request.META:
                    # Now that we know they provided a resource, let's check to see if it exists.
                    try:
                        resource = Resource.objects.get(
                            name=request.META['HTTP_RESTBROKER_RESOURCE'],
                            project=api_key.project
                        )

                        # The resource does exist! Now we need to go through the request and check to see
                        # if what is required has been sent.

                        # Create a resource_request object that holds all data as we move futher through
                        resource_request = {}

                        # HEADERS CHECK
                        # We need to check and see if there are headers.
                        resource_headers = ResourceHeader.objects.all().filter(resource=resource)

                        # Create a list of the provided headers and their values
                        provided_headers = []

                        # If there are headers
                        if resource_headers:
                            # Loop through each header and check to see if it exists in the request
                            for header in resource_headers:
                                # Check to see if that one is present. HTTP_+header name with dashes replaced with underscores.
                                if 'HTTP_'+header.key.upper().replace('-', '_') in request.META:
                                    # Does exist.
                                    single_header_object = {
                                        'obj': header,
                                        'provided_value': request.META['HTTP_'+header.key.upper().replace('-', '_')]
                                    }

                                    # Append it to the users provided headers
                                    provided_headers.append(single_header_object)
                                else:
                                    # This means a required header is not provided so record it and respond
                                    api_request = APIRequest(
                                        authentication_type='KEY',
                                        type=request.method,
                                        url=request.get_full_path(),
                                        status='400 ERR',
                                        ip_address=get_client_ip(request),
                                        source=request.META['HTTP_USER_AGENT'],
                                        api_key=api_key
                                    )

                                    api_request.save()

                                    response = {
                                        'error': {
                                            'message': 'Your request is missing a required header. Missing header is: '+header.key,
                                            'type': 'missing_header'
                                        }
                                    }

                                    return HttpResponse(json.dumps(response), content_type='application/json')

                        # If we got here we either have a list with no headers or a list with headers that have values.
                        # Either way, if the incorrect values were given we would not be here.
                        resource_request['headers'] = provided_headers

                        # GET PARAMETER CHECK
                        # Now we have looked at headers, lets do the same with GET parameters.
                        resource_parameters = ResourceParameter.objects.all().filter(resource=resource)

                        # Create a list of provided resources
                        provided_parameters = []

                        # If there are resource parameters, i.e GET URL parameters
                        if resource_parameters:
                            # Loop through each parameter
                            for parameter in resource_parameters:
                                # Check to see if that was provided
                                if parameter.key in request.GET:
                                    # It is provided so lets get it.
                                    single_parameter_obj = {
                                        'obj': parameter,
                                        'provided_value': request.GET[parameter.key]
                                    }

                                    # Append it to the list of provided parameters
                                    provided_parameters.append(single_parameter_obj)
                                else:
                                    # This means a required header is not provided so record it and respond
                                    api_request = APIRequest(
                                        authentication_type='KEY',
                                        type=request.method,
                                        url=request.get_full_path(),
                                        status='400 ERR',
                                        ip_address=get_client_ip(request),
                                        source=request.META['HTTP_USER_AGENT'],
                                        api_key=api_key
                                    )

                                    api_request.save()

                                    response = {
                                        'error': {
                                            'message': 'Your request is missing a required GET parameter. Missing parameter is: ' + parameter.key,
                                            'type': 'missing_parameter'
                                        }
                                    }

                                    return HttpResponse(json.dumps(response), content_type='application/json')

                        # Like with headers, if we have gotten here we have analysed the correct GET parameters
                        resource_request['parameters'] = provided_parameters

                        # GET THE COLUMNS TO RETURN
                        # Now we need to start constructing a response.
                        # We first need to find out what columns and from what tables need to be returned before we generate SQL.
                        data_source_columns = ResourceDataSourceColumn.objects.all().filter(resource=resource)

                        # Create empty dictionary of columns that need to be returned
                        columns_to_return = {}

                        for data_source_column in data_source_columns:
                            # Get its relevant database column from the database
                            database_column = DatabaseColumn.objects.get(id=int(data_source_column.column_id))

                            # Check if the table that this column is part of is already in the list
                            if database_column.table.name in columns_to_return:
                                # Then add just this column to the list of columns to return from this table
                                columns_to_return[database_column.table.name].append(database_column)
                            else:
                                # It doesn't exist so create it.
                                columns_to_return[database_column.table.name] = [database_column]

                        # Now add it to the resource_request
                        resource_request['columns_to_return'] = columns_to_return

                        # GET THE FILTERS AND CHECK THAT THEY ARE POSSIBLE AND RETURN IF SO.

                        # DO SOME SQL.
                        # Get the SQL information
                        database = Database.objects.get(project=resource.project)

                        # Construct the sql query
                        sql_query = ''

                        # Loop through each table
                        for table_index, (table, columns) in enumerate(resource_request['columns_to_return'].items()):
                            single_table_query = 'SELECT '
                            # Loop through columns
                            for index, column in enumerate(columns):
                                single_table_query += column.name

                                # If we are in any iteration apart from the last add a comma and space
                                if(index < len(columns)-1):
                                    single_table_query += ', '

                            # Add the table
                            single_table_query += ' FROM '+table+''

                            # Check if we are in the last table, if not then add UNION as we want to UNION all of the tables.
                            # If not just return a semi colon to end the statement
                            if table_index < len(resource_request['columns_to_return'].keys())-1:
                                single_table_query += ' UNION '
                            else:
                                # Last table, complete the query
                                single_table_query += ';'

                            sql_query += single_table_query

                        # Try connect to the server and do database things.
                        try:

                            conn = db.connect(host=database.server_address, port=3306,
                                          user=database.user, password=database.password,
                                          database=database.name)


                            # Create a cursor
                            cursor = conn.cursor()

                            # Execute the query
                            cursor.execute(sql_query)

                            for row in cursor:
                                print(row)

                        except Exception as e:
                            print(e)
                            # Cannot connect to the server. Record it and respond
                            api_request = APIRequest(
                                authentication_type='KEY',
                                type=request.method,
                                url=request.get_full_path(),
                                status='402 ERR',
                                ip_address=get_client_ip(request),
                                source=request.META['HTTP_USER_AGENT'],
                                api_key=api_key
                            )

                            api_request.save()

                            # Create a response
                            response = {
                                'error': {
                                    'message': 'There was an error with the interaction between us and your database. Please see the error generated by your server below.',
                                    'type': 'error_connecting_to_database',
                                    'database_error': str(e)
                                }
                            }

                            return HttpResponse(json.dumps(response), content_type='application/json')


                    except Exception as e:
                        print(e)
                        # Resource does not exist. Record the request.
                        api_request = APIRequest(
                            authentication_type='KEY',
                            type=request.method,
                            url=request.get_full_path(),
                            status='404 ERR',
                            ip_address=get_client_ip(request),
                            source=request.META['HTTP_USER_AGENT'],
                            api_key=api_key
                        )

                        api_request.save()

                        # Create a response
                        response = {
                            'error': {
                                'message': 'The resource that was requested does not exist.',
                                'type': 'resource_doesnt_exist'
                            }
                        }

                        return HttpResponse(json.dumps(response), content_type='application/json')
                else:
                    # The resource was not provided. Record the requst
                    api_request = APIRequest(
                        authentication_type='KEY',
                        type=request.method,
                        url=request.get_full_path(),
                        status='400 ERR',
                        ip_address=get_client_ip(request),
                        source=request.META['HTTP_USER_AGENT'],
                        api_key=api_key
                    )

                    api_request.save()

                    # Create a response
                    response = {
                        'error': {
                            'message': 'No resource was provided. RESTBroker cannot tell what you are trying to access.',
                            'type': 'no_resource_provided'
                        }
                    }

                    return HttpResponse(json.dumps(response), content_type='application/json')

            except Exception as e:
                # API Key is not found
                # It was not provided. Construct a response to send back and log the request.
                api_request = APIRequest(
                    authentication_type='NO_AUTH',
                    type=request.method,
                    url=request.get_full_path(),
                    status='401 ERR',
                    ip_address=get_client_ip(request),
                    source=request.META['HTTP_USER_AGENT']
                )

                api_request.save()

                # Create a response
                response = {
                    'error': {
                        'message': 'The provided API Key is invalid. Please ensure it is correctly inputted.',
                        'type': 'bad_api_key'
                    }
                }

                return HttpResponse(json.dumps(response), content_type='application/json')

        else:
            # It was not provided. Construct a response to send back and log the request.
            api_request = APIRequest(
                authentication_type='NO_AUTH',
                type=request.method,
                url=request.get_full_path(),
                status='401 ERR',
                ip_address=get_client_ip(request),
                source=request.META['HTTP_USER_AGENT']
            )

            api_request.save()

            # Create a response
            response = {
                'error': {
                    'message': 'API Key not provided. Please provide a relevant API key in the HTTP_AUTHORIZATION header in the username field.',
                    'type': 'no_api_key'
                }
            }

            return HttpResponse(json.dumps(response), content_type='application/json')


# The main view that handles Public API request. Differs to Private as it requires the project ID as no
# API is required
class RequestHandlerPublic(View):

    # First handle GET requests
    def get(self, request, project_id):
        print(project_id)