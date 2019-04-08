import ast
import base64
import json
from datetime import datetime

import dicttoxml
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

import MySQLdb as db

# The main view that handles Private API requests
import redis

from api.models import APIRequest, APIKey
from core.models import Resource, ResourceParameter, ResourceHeader, ResourceDataSourceColumn, DatabaseColumn, Database, \
    ResourceDataSourceFilter, DatabaseTable, ResourceParentChildRelationship, BlockedIP, ResourceDataBind, \
    ResourceUserGroup, ResourceTextSource


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_REAL_IP')
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
            api_key = base64.b64decode(request.META['HTTP_AUTHORIZATION'].split('Basic ', 1)[1])[:-1].decode('utf-8')

            # Look up API key
            try:
                api_key = APIKey.objects.get(key=api_key)

                # Check to see if the requesters IP is blocked
                ip = get_client_ip(request)

                try:
                    blocked_ip = BlockedIP.objects.get(ip_address=ip)

                    response = json.dumps({
                        'error': {
                            'message': 'Requests from this IP are blocked',
                            'type': 'blocked_ip'
                        }
                    })

                    # This means it does exist so send a return message.
                    api_request = APIRequest(
                        authentication_type='KEY',
                        type=request.method,
                        resource=request.META['HTTP_RESOURCE'],
                        url=request.get_full_path(),
                        status='403 ERR',
                        ip_address=get_client_ip(request),
                        source=request.META['HTTP_USER_AGENT'],
                        api_key=api_key,
                        response_to_user=response
                    )

                    api_request.save()

                    return HttpResponse(response, content_type='application/json', status=403)

                except:
                    # If it doesn't exist then just pass and continue
                    pass

                # API Key is found. No check for a resource.
                if 'HTTP_RESOURCE' in request.META:
                    # Now that we know they provided a resource, let's check to see if it exists.
                    try:
                        resource = Resource.objects.get(
                            name=request.META['HTTP_RESOURCE'],
                            project=api_key.project,
                            request_type='GET'
                        )

                        # Check to see if the resource is "turned off"
                        if not resource.status:
                            response = {
                                'error': {
                                    'message': 'The owner of this resource has it disabled/off. Check back later as it may be enabled/turned on',
                                    'type': 'endpoint_off'
                                }
                            }

                            if resource.response_format == 'JSON':
                                return HttpResponse(json.dumps(response), content_type='application/json')
                            elif resource.response_format == 'XML':
                                return HttpResponse(dicttoxml.dicttoxml(response), content_type='application/xml')

                        # Now we have the API Key. Let's make sure that the groups match.
                        user_groups = ResourceUserGroup.objects.all().filter(resource=resource)

                        # We only check for user groups if they are present or if the api_key doesn't contain master
                        if user_groups and 'rb_mstr_key_' not in api_key.key:
                            # If the api_key has a user group attached to it
                            # If it doesn't ignore it
                            if api_key.user_group:
                                # Check to see if that user_group is in the set user_groups. If not then say permission denied
                                in_group = False
                                for user_group in user_groups:
                                    if api_key.user_group == user_group.user_group:
                                        in_group = True

                                if in_group is False:

                                    response = {
                                        'error': {
                                            'message': 'Permission Denied. Your API Key/User Group doesn\'t allow you to access that resource.',
                                            'type': 'permission_denied'
                                        }
                                    }

                                    if resource.response_format == 'JSON':
                                        response = json.dumps(response)
                                    elif resource.response_format == 'XML':
                                        response = dicttoxml.dicttoxml(response)

                                    # This means a required header is not provided so record it and respond
                                    api_request = APIRequest(
                                        authentication_type='KEY',
                                        type=request.method,
                                        resource=request.META['HTTP_RESOURCE'],
                                        url=request.get_full_path(),
                                        status='403 ERR',
                                        ip_address=get_client_ip(request),
                                        source=request.META['HTTP_USER_AGENT'],
                                        api_key=api_key,
                                        response_to_user=response
                                    )

                                    api_request.save()

                                    if resource.response_format == 'JSON':
                                        return HttpResponse(response, content_type='application/json', status=403)
                                    elif resource.response_format == 'XML':
                                        return HttpResponse(response,
                                                            content_type='application/xml', status=403)

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
                                if 'HTTP_' + header.key.upper().replace('-', '_') in request.META:
                                    # Does exist.
                                    single_header_object = {
                                        'obj': header,
                                        'provided_value': request.META['HTTP_' + header.key.upper().replace('-', '_')]
                                    }

                                    # Append it to the users provided headers
                                    provided_headers.append(single_header_object)
                                else:
                                    response = {
                                        'error': {
                                            'message': 'Your request is missing a required header. Missing header is: ' + header.key,
                                            'type': 'missing_header'
                                        }
                                    }

                                    if resource.response_format == 'JSON':
                                        response = json.dumps(response)
                                    elif resource.response_format == 'XML':
                                        response = dicttoxml.dicttoxml(response)

                                    # This means a required header is not provided so record it and respond
                                    api_request = APIRequest(
                                        authentication_type='KEY',
                                        type=request.method,
                                        resource=request.META['HTTP_RESOURCE'],
                                        url=request.get_full_path(),
                                        status='400 ERR',
                                        ip_address=get_client_ip(request),
                                        source=request.META['HTTP_USER_AGENT'],
                                        api_key=api_key,
                                        response_to_user=response
                                    )

                                    api_request.save()

                                    if resource.response_format == 'JSON':
                                        return HttpResponse(response, content_type='application/json', status=400)
                                    elif resource.response_format == 'XML':
                                        return HttpResponse(response,
                                                            content_type='application/xml', status=400)

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
                                    response = {
                                        'error': {
                                            'message': 'Your request is missing a required GET parameter. Missing parameter is: ' + parameter.key,
                                            'type': 'missing_parameter'
                                        }
                                    }

                                    if resource.response_format == 'JSON':
                                        response = json.dumps(response)
                                    elif resource.response_format == 'XML':
                                        response = dicttoxml.dicttoxml(response)

                                    # This means a required header is not provided so record it and respond
                                    api_request = APIRequest(
                                        authentication_type='KEY',
                                        type=request.method,
                                        resource=request.META['HTTP_RESOURCE'],
                                        url=request.get_full_path(),
                                        status='400 ERR',
                                        ip_address=get_client_ip(request),
                                        source=request.META['HTTP_USER_AGENT'],
                                        api_key=api_key,
                                        response_to_user=response
                                    )

                                    api_request.save()

                                    if resource.response_format == 'JSON':
                                        return HttpResponse(response, content_type='application/json', status=400)
                                    elif resource.response_format == 'XML':
                                        return HttpResponse(response,
                                                            content_type='application/xml', status=400)

                        # Like with headers, if we have gotten here we have analysed the correct GET parameters
                        resource_request['parameters'] = provided_parameters

                        # Value to determine if the resulting response should be saved to Redis
                        need_to_be_cached = False

                        # Let us check to see if the user has caching on. If they do then we can check Redis for cached results
                        if resource.project.caching:
                            # Now that we know that caching is enabled. Check to see if there has been any stores today of this cache
                            # Let's connect to Redis
                            r = redis.Redis(host='127.0.0.1', port=6379, db=0)

                            # Now we have a connection, check to see if there is a cache with todays timestamp
                            if r.get(datetime.now().strftime('%Y-%m-%d:%H')):
                                # So there is a cache from the last hour. This means that we now need to basically look
                                # through all requests to this resource and see if any of them have happened in this hour
                                # of this day. If they have then we must let SQL do its thing, else we can just returned the
                                # Redis cache.
                                day = datetime.today().strftime('%d')
                                month = datetime.today().strftime('%m')
                                year = datetime.today().strftime('%Y')
                                hour = datetime.today().strftime('%H')

                                # Get all POST requests
                                post_requests = APIRequest.objects.all().filter(
                                    type='POST',
                                    resource=resource.name,
                                    date__day=day,
                                    date__month=month,
                                    date__year=year,
                                    date__hour=hour
                                )

                                # Get all DELETE requests
                                delete_requests = APIRequest.objects.all().filter(
                                    type='DELETE',
                                    resource=resource.name,
                                    date__day=day,
                                    date__month=month,
                                    date__year=year,
                                    date__hour=hour
                                )

                                return HttpResponse(json.dumps({'howya': 'howya'}), content_type='application/json')

                                # So if neither have entries then we can return the Redis result
                                # Any future checks here to whether or not the data has been modified
                                # would go here
                                if not post_requests and not delete_requests:

                                    # Now that we know there hasn't been POSTs or DELETEs to any other resource with the same name, we still
                                    # have to find out if any tables have been involved in POSTs that are included in this resource.
                                    # First get the tables.
                                    # We can do this here while we have access to that objects
                                    data_source_columns = ResourceDataSourceColumn.objects.all().filter(
                                        resource=resource)

                                    tables_included = []

                                    for data_source_column in data_source_columns:
                                        # Get the the table from that column
                                        table = DatabaseColumn.objects.get(id=int(data_source_column.column_id)).table
                                        if table not in tables_included:
                                            tables_included.append(table)

                                    unsafe_api_requests_list = []
                                    # Now we have to check if there have been any POST or DELETE API requests where they have not been cached
                                    # with the hour as now. If there aren't then just return the cache, if there are then do SQL and cache.
                                    unsafe_api_requests = APIRequest.objects.all().filter(
                                        Q(type='POST') | Q(type='DELETE'),
                                        date__day=day,
                                        date__month=month,
                                        date__year=year,
                                        date__hour=hour,
                                        cache=False)

                                    # We need to loop through each request, see if any of the tables it has are in tables_included
                                    for unsafe_api_request in unsafe_api_requests:
                                        # This will basically get the tables involved in this request by first filtering by resource name and request type.
                                        # Then it will only take the column.table value and make sure it only takes distinct values
                                        unsafe_api_request_data_binds = ResourceDataBind.objects.all().filter(
                                            resource=Resource.objects.get(name=unsafe_api_request.resource,
                                                                          request_type=unsafe_api_request.type))

                                        # Value to see if there is table sharing going on
                                        shares_table = False

                                        # Loop through each one
                                        for unsafe_api_request_data_bind in unsafe_api_request_data_binds:
                                            if unsafe_api_request_data_bind.column.table in tables_included:
                                                shares_table = True
                                            else:
                                                shares_table = False

                                        # So if this particular API request does share a table then add it to the list, if it doesn't then don't
                                        if shares_table:
                                            unsafe_api_requests_list.append(unsafe_api_request)

                                    # If there have been requests that have gone unaccounted then we can't return cache and we need to
                                    # make a new cache
                                    if not unsafe_api_requests_list:
                                        # If its empty then just return the cached result
                                        data = json.loads(r.get(datetime.today().strftime('%Y-%m-%d:%H')))

                                        # Add the API request
                                        api_request = APIRequest(
                                            authentication_type='KEY',
                                            type=request.method,
                                            resource=request.META['HTTP_RESOURCE'],
                                            url=request.get_full_path(),
                                            status='200 OK',
                                            ip_address=get_client_ip(request),
                                            source=request.META['HTTP_USER_AGENT'],
                                            api_key=api_key,
                                            cached_result=True
                                        )

                                        api_request.save()

                                        resource_text_sources = ResourceTextSource.objects.all().filter(
                                            resource=resource)

                                        text_response = ''

                                        if resource_text_sources:
                                            for resource_text_source in resource_text_sources:
                                                text_response += resource_text_source.text

                                        # Check if there was text sources, if there is then try merge them
                                        data = {**data, **ast.literal_eval(text_response)}

                                        if resource.response_format == 'JSON':
                                            return HttpResponse(json.dumps(data), content_type='application/json',
                                                                status=200)
                                        elif resource.response_format == 'XML':
                                            return HttpResponse(dicttoxml.dicttoxml(data),
                                                                content_type='application/xml', status=200)
                                    else:
                                        need_to_be_cached = True
                                else:
                                    # If not then we need to cache
                                    need_to_be_cached = True
                            else:
                                # There is no cache so just run the SQL and save the cache for later.
                                need_to_be_cached = True

                        if need_to_be_cached or resource.project.caching is False:
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

                            # Dictionary to hold the data that is returned from the database.
                            data_from_database = {}

                            # Try connect to the server and do database things.
                            try:
                                conn = db.connect(host=database.server_address, port=3306,
                                                  user=database.user, password=database.password,
                                                  database=database.name, connect_timeout=4)

                                # Construct the sql query
                                sql_query = ''

                                # Loop through each table
                                for table_index, (table, columns) in enumerate(
                                        resource_request['columns_to_return'].items()):

                                    # Create a cursor
                                    cursor = conn.cursor()

                                    single_table_query = 'SELECT '
                                    # Loop through columns
                                    for index, column in enumerate(columns):
                                        single_table_query += column.name

                                        # If we are in any iteration apart from the last add a comma and space
                                        if (index < len(columns) - 1):
                                            single_table_query += ', '

                                    # Add the table
                                    single_table_query += ' FROM ' + table + ''

                                    # Append the end with a semi colon to end the query
                                    single_table_query += ';'

                                    # Now that we have the single query, execute it.
                                    cursor.execute(single_table_query)

                                    column_names = [i[0] for i in cursor.description]

                                    # Loop through the results
                                    for row in cursor:
                                        single_table_object = {}

                                        # We need to loop through the columns in this row and match them to the column names
                                        for index, db_column in enumerate(row):
                                            # Put whatever column name in order that we got from SQL matched with its value
                                            single_table_object[column_names[index]] = db_column

                                        # Check to see if the table is already in the data_from_database dict
                                        if table in data_from_database:
                                            # If it is then we append.
                                            data_from_database[table].append(single_table_object)
                                        else:
                                            # If not we create
                                            data_from_database[table] = [single_table_object]

                                conn.close()

                                # Now lets look for the parent child relationships
                                parent_child_relationships = ResourceParentChildRelationship.objects.all().filter(
                                    resource=resource)

                                for relationship in parent_child_relationships:
                                    # Loop through the data
                                    for value, data in data_from_database.items():
                                        # Check to see if the table is a parent
                                        try:
                                            this_relationship = ResourceParentChildRelationship.objects.get(
                                                resource=resource,
                                                parent_table=DatabaseTable.objects.get(database=database, name=value))

                                            for instance in data:
                                                # Delete the column with the name of
                                                instance[this_relationship.child_table.name] = list(filter(
                                                    lambda single_instance: single_instance[
                                                                                this_relationship.child_table_column.name] ==
                                                                            instance[
                                                                                this_relationship.parent_table_column.name],
                                                    data_from_database[this_relationship.child_table.name]))

                                        except Exception as e:
                                            print(e)

                                    # Delete the child value from the data
                                    try:
                                        del data_from_database[relationship.child_table.name]

                                    except Exception as e:
                                        print('Cannot find that value.')

                                # Cannot connect to the server. Record it and respond
                                api_request = APIRequest(
                                    authentication_type='KEY',
                                    type=request.method,
                                    resource=request.META['HTTP_RESOURCE'],
                                    url=request.get_full_path(),
                                    status='200 OK',
                                    ip_address=get_client_ip(request),
                                    source=request.META['HTTP_USER_AGENT'],
                                    api_key=api_key
                                )

                                api_request.save()

                                # Let's check to see if we were meant to save the cache
                                if need_to_be_cached:
                                    r = redis.Redis(host='127.0.0.1', port=6379, db=0)

                                    today = datetime.now()

                                    # Set the dict
                                    r.psetex(name=today.strftime('%Y-%m-%d:%H'),
                                             time_ms=((int(resource.project.caching_expiry) * 60) * 60) * 1000,
                                             value=str(json.dumps(data_from_database)))

                                    # Loop through the last unsafe HTTP requests in the last hour and mark them as cached.
                                    unsafe_api_requests = APIRequest.objects.all().filter(
                                        Q(type='POST') | Q(type='DELETE'),
                                        date__day=today.day,
                                        date__month=today.month,
                                        date__year=today.year,
                                        date__hour=today.hour)

                                    # Marking them as cached.
                                    for api_request in unsafe_api_requests:
                                        api_request.cache = True
                                        api_request.save()

                                if resource.response_format == 'JSON':
                                    return HttpResponse(json.dumps(data_from_database), content_type='application/json',
                                                        status=200)
                                elif resource.response_format == 'XML':
                                    return HttpResponse(dicttoxml.dicttoxml(data_from_database),
                                                        content_type='application/xml', status=200)

                            except Exception as e:
                                print(e)
                                # Create a response
                                response = {
                                    'error': {
                                        'message': 'There was an error with the interaction between us and your database. Please see the error generated by your server below.',
                                        'type': 'database_error',
                                        'database_error': str(e)
                                    }
                                }

                                if resource.response_format == 'JSON':
                                    response = json.dumps(response)
                                elif resource.response_format == 'XML':
                                    response = dicttoxml.dicttoxml(response)

                                # Cannot connect to the server. Record it and respond
                                api_request = APIRequest(
                                    authentication_type='KEY',
                                    type=request.method,
                                    resource=request.META['HTTP_RESOURCE'],
                                    url=request.get_full_path(),
                                    status='402 ERR',
                                    ip_address=get_client_ip(request),
                                    source=request.META['HTTP_USER_AGENT'],
                                    api_key=api_key,
                                    response_to_user=response
                                )

                                api_request.save()

                                if resource.response_format == 'JSON':
                                    return HttpResponse(response, content_type='application/json', status=402)
                                elif resource.response_format == 'XML':
                                    return HttpResponse(response,
                                                        content_type='application/xml', status=402)

                    except Exception as e:
                        print(e)
                        # Create a response
                        response = {
                            'error': {
                                'message': 'The resource that was requested does not exist.',
                                'type': 'resource_doesnt_exist',
                                'error': str(e)
                            }
                        }

                        if resource.response_format == 'JSON':
                            response = json.dumps(response)
                        elif resource.response_format == 'XML':
                            response = dicttoxml.dicttoxml(response)

                        # Resource does not exist. Record the request.
                        api_request = APIRequest(
                            authentication_type='KEY',
                            type=request.method,
                            resource=request.META['HTTP_RESOURCE'],
                            url=request.get_full_path(),
                            status='404 ERR',
                            ip_address=get_client_ip(request),
                            source=request.META['HTTP_USER_AGENT'],
                            api_key=api_key,
                            response_to_user=response
                        )

                        api_request.save()

                        if resource.response_format == 'JSON':
                            return HttpResponse(response, content_type='application/json', status=404)
                        elif resource.response_format == 'XML':
                            return HttpResponse(response,
                                                content_type='application/xml', status=404)
                else:
                    # Create a response
                    response = json.dumps({
                        'error': {
                            'message': 'No resource was provided. Lapis cannot tell what you are trying to access.',
                            'type': 'no_resource_provided'
                        }
                    })

                    # The resource was not provided. Record the requst
                    api_request = APIRequest(
                        authentication_type='KEY',
                        type=request.method,
                        url=request.get_full_path(),
                        status='400 ERR',
                        ip_address=get_client_ip(request),
                        source=request.META['HTTP_USER_AGENT'],
                        api_key=api_key,
                        response_to_user=response
                    )

                    api_request.save()

                    return HttpResponse(response, content_type='application/json', status=400)

            except Exception as e:
                # API Key is not found
                # Create a response
                response = json.dumps({
                    'error': {
                        'message': 'The provided API Key is invalid. Please ensure it is correctly inputted.',
                        'type': 'bad_api_key'
                    }
                })

                # It was not provided. Construct a response to send back and log the request.
                api_request = APIRequest(
                    authentication_type='NO_AUTH',
                    type=request.method,
                    url=request.get_full_path(),
                    status='401 ERR',
                    ip_address=get_client_ip(request),
                    source=request.META['HTTP_USER_AGENT'],
                    response_to_user=response
                )

                api_request.save()

                return HttpResponse(response, content_type='application/json', status=401)

        else:
            # Create a response
            response = json.dumps({
                'error': {
                    'message': 'API Key not provided. Please provide a relevant API key in the HTTP_AUTHORIZATION header in the username field.',
                    'type': 'no_api_key'
                }
            })

            # It was not provided. Construct a response to send back and log the request.
            api_request = APIRequest(
                authentication_type='NO_AUTH',
                type=request.method,
                url=request.get_full_path(),
                status='401 ERR',
                ip_address=get_client_ip(request),
                source=request.META['HTTP_USER_AGENT'],
                response_to_user=response,
            )

            api_request.save()

            return HttpResponse(response, content_type='application/json', status=401)


    # First handle POST requests
    def post(self, request):

        # The first thing we need to do is check to see if the header information has been sent for authorisation etc.
        if 'HTTP_AUTHORIZATION' in request.META:
            # Access GET params: print(request.GET)
            # The key was provided so check it. First we need to base64 decode the key.
            # Extract the key from the string. Base64decode, remove the last colon, and decode to utf-8 rather than bytes
            api_key = base64.b64decode(request.META['HTTP_AUTHORIZATION'].split('Basic ', 1)[1])[:-1].decode(
                'utf-8')

            # Look up API key
            try:
                api_key = APIKey.objects.get(key=api_key)

                # Check to see if the requesters IP is blocked
                ip = get_client_ip(request)

                try:
                    blocked_ip = BlockedIP.objects.get(ip_address=ip)

                    response = json.dumps({
                        'error': {
                            'message': 'Requests from this IP are blocked',
                            'type': 'blocked_ip'
                        }
                    })

                    # This means it does exist so send a return message.
                    api_request = APIRequest(
                        authentication_type='KEY',
                        type=request.method,
                        resource=request.META['HTTP_RESOURCE'],
                        url=request.get_full_path(),
                        status='403 ERR',
                        ip_address=get_client_ip(request),
                        source=request.META['HTTP_USER_AGENT'],
                        api_key=api_key,
                        response_to_user=response
                    )

                    api_request.save()

                    return HttpResponse(response, content_type='application/json', status=403)

                except:
                    # If it doesn't exist then just pass and continue
                    pass

                # API Key is found. No check for a resource.
                if 'HTTP_RESOURCE' in request.META:
                    # Now that we know they provided a resource, let's check to see if it exists.
                    try:
                        resource = Resource.objects.get(
                            name=request.META['HTTP_RESOURCE'],
                            project=api_key.project,
                            request_type=request.method
                        )

                        # Check to see if the resource is "turned off"
                        if not resource.status:
                            response = json.dumps({
                                'error': {
                                    'message': 'The owner of this resource has it disabled/off. Check back later as it may be enabled/turned on',
                                    'type': 'endpoint_off'
                                }
                            })

                            return HttpResponse(response, content_type='application/json')

                        # Now we have the API Key. Let's make sure that the groups match.
                        user_groups = ResourceUserGroup.objects.all().filter(resource=resource)

                        # We only check for user groups if they are present or if the api_key doesn't contain master
                        if user_groups and 'rb_mstr_key_' not in api_key.key:
                            # If the api_key has a user group attached to it
                            # If it doesn't ignore it
                            if api_key.user_group:
                                # Check to see if that user_group is in the set user_groups. If not then say permission denied
                                in_group = False
                                for user_group in user_groups:
                                    if api_key.user_group == user_group.user_group:
                                        in_group = True

                                if in_group is False:
                                    response = json.dumps({
                                        'error': {
                                            'message': 'Permission Denied. Your API Key/User Group doesn\'t allow you to access that resource.',
                                            'type': 'permission_denied'
                                        }
                                    })

                                    # This means a required header is not provided so record it and respond
                                    api_request = APIRequest(
                                        authentication_type='KEY',
                                        type=request.method,
                                        resource=request.META['HTTP_RESOURCE'],
                                        url=request.get_full_path(),
                                        status='403 ERR',
                                        ip_address=get_client_ip(request),
                                        source=request.META['HTTP_USER_AGENT'],
                                        api_key=api_key,
                                        response_to_user=response
                                    )

                                    api_request.save()

                                    return HttpResponse(response, content_type='application/json', status=403)

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
                                if 'HTTP_' + header.key.upper().replace('-', '_') in request.META:
                                    # Does exist.
                                    single_header_object = {
                                        'obj': header,
                                        'provided_value': request.META[
                                            'HTTP_' + header.key.upper().replace('-', '_')]
                                    }

                                    # Append it to the users provided headers
                                    provided_headers.append(single_header_object)
                                else:

                                    response = json.dumps({
                                        'error': {
                                            'message': 'Your request is missing a required header. Missing header is: ' + header.key,
                                            'type': 'missing_header'
                                        }
                                    })

                                    # This means a required header is not provided so record it and respond
                                    api_request = APIRequest(
                                        authentication_type='KEY',
                                        type=request.method,
                                        resource=request.META['HTTP_RESOURCE'],
                                        url=request.get_full_path(),
                                        status='400 ERR',
                                        ip_address=get_client_ip(request),
                                        source=request.META['HTTP_USER_AGENT'],
                                        api_key=api_key,
                                        response_to_user=response
                                    )

                                    api_request.save()

                                    return HttpResponse(response, content_type='application/json',
                                                        status=400)

                        # If we got here we either have a list with no headers or a list with headers that have values.
                        # Either way, if the incorrect values were given we would not be here.
                        resource_request['headers'] = provided_headers

                        # Get the databinds
                        data_binds = ResourceDataBind.objects.all().filter(resource=resource)

                        data_bind_tables = {

                        }

                        if data_binds:
                            full_sql = ''

                            # We need to basically loop through each data bind and make it so that they are sorted by table.
                            # This way we can execute multiple INSERTS to different tables.
                            for data_bind in data_binds:

                                # If the table is already listed then just append this data bind.
                                if data_bind.column.table.name in data_bind_tables:
                                    data_bind_tables[data_bind.column.table.name].append(data_bind)
                                else:
                                    data_bind_tables[data_bind.column.table.name] = [data_bind]

                            # Now we have it in a dictionary form.
                            for table, columns in data_bind_tables.items():
                                # This is one single table so do this
                                sql = 'INSERT INTO '+table+' ('

                                # Map through the columns
                                column_part = ', '.join(list(map(lambda column: column.column.name, columns)))

                                sql += column_part+') '

                                values_part = ''

                                # Now get the values for the insert
                                for index, column in enumerate(columns):
                                    if column.key not in request.POST:

                                        response = json.dumps({
                                            'error': {
                                                'message': 'Your request is missing a POST attribute. Missing attribute is: ' + column.key,
                                                'type': 'missing_attribute'
                                            }
                                        })

                                        # This means a required header is not provided so record it and respond
                                        api_request = APIRequest(
                                            authentication_type='KEY',
                                            type=request.method,
                                            resource=request.META['HTTP_RESOURCE'],
                                            url=request.get_full_path(),
                                            status='400 ERR',
                                            ip_address=get_client_ip(request),
                                            source=request.META['HTTP_USER_AGENT'],
                                            api_key=api_key,
                                            response_to_user=response
                                        )

                                        api_request.save()

                                        return HttpResponse(response, content_type='application/json',
                                                            status=400)
                                    else:
                                        # It is present, so first get the value
                                        posted_value = request.POST[column.key]

                                        if column.type == 'String':
                                            values_part += '"' + posted_value + '"'
                                        else:
                                            values_part += posted_value

                                        if index < (len(columns)) - 1:
                                            values_part += ', '
                                        else:
                                            values_part += ')'

                                sql += 'VALUES ('+values_part+'; '

                                # Add it to the big whole SQL statement
                                full_sql += sql

                            # Try connect to the server and do database things.
                            try:
                                database = Database.objects.get(project=resource.project)

                                conn = db.connect(host=database.server_address, port=3306,
                                                  user=database.user, password=database.password,
                                                  database=database.name, connect_timeout=4)

                                # Create a cursor
                                cursor = conn.cursor()

                                # Now that we have the single query, execute it.
                                cursor.execute(full_sql)

                                # Commit the result
                                conn.commit()

                                for row in cursor:
                                    print(row)

                                conn.close()

                                # Cannot connect to the server. Record it and respond
                                api_request = APIRequest(
                                    authentication_type='KEY',
                                    type=request.method,
                                    resource=request.META['HTTP_RESOURCE'],
                                    url=request.get_full_path(),
                                    status='200 OK',
                                    ip_address=get_client_ip(request),
                                    source=request.META['HTTP_USER_AGENT'],
                                    api_key=api_key
                                )

                                api_request.save()

                                # DO POST RESPONSE STUFF
                                # Check to see if there a response text sources.
                                resource_text_sources = ResourceTextSource.objects.all().filter(resource=resource)

                                response = ''

                                if resource_text_sources:
                                    for resource_text_source in resource_text_sources:
                                        response += resource_text_source.text

                                # Return it
                                if resource.response_format == 'JSON':
                                    return HttpResponse(response, content_type='application/json', status=200)


                            except Exception as e:
                                print(e)
                                # Create a response
                                response = json.dumps({
                                    'error': {
                                        'message': 'There was an error with the interaction between us and your database. Please see the error generated by your server below.',
                                        'type': 'database_error',
                                        'database_error': str(e)
                                    }
                                })

                                # Cannot connect to the server. Record it and respond
                                api_request = APIRequest(
                                    authentication_type='KEY',
                                    type=request.method,
                                    resource=request.META['HTTP_RESOURCE'],
                                    url=request.get_full_path(),
                                    status='402 ERR',
                                    ip_address=get_client_ip(request),
                                    source=request.META['HTTP_USER_AGENT'],
                                    api_key=api_key,
                                    response_to_user=response
                                )

                                api_request.save()

                                return HttpResponse(response, content_type='application/json', status=402)

                    except Exception as e:

                        # Create a response
                        response = json.dumps({
                            'error': {
                                'message': 'The resource that was requested does not exist.',
                                'type': 'resource_doesnt_exist'
                            }
                        })

                        # Resource does not exist. Record the request.
                        api_request = APIRequest(
                            authentication_type='KEY',
                            type=request.method,
                            resource=request.META['HTTP_RESOURCE'],
                            url=request.get_full_path(),
                            status='404 ERR',
                            ip_address=get_client_ip(request),
                            source=request.META['HTTP_USER_AGENT'],
                            api_key=api_key,
                            response_to_user=response
                        )

                        api_request.save()

                        return HttpResponse(response, content_type='application/json', status=404)
                else:

                    # Create a response
                    response = json.dumps({
                        'error': {
                            'message': 'No resource was provided. Lapis cannot tell what you are trying to access.',
                            'type': 'no_resource_provided'
                        }
                    })

                    # The resource was not provided. Record the requst
                    api_request = APIRequest(
                        authentication_type='KEY',
                        type=request.method,
                        url=request.get_full_path(),
                        status='400 ERR',
                        ip_address=get_client_ip(request),
                        source=request.META['HTTP_USER_AGENT'],
                        api_key=api_key,
                        response_to_user=response
                    )

                    api_request.save()

                    return HttpResponse(response, content_type='application/json', status=400)

            except Exception as e:

                # Create a response
                response = json.dumps({
                    'error': {
                        'message': 'The provided API Key is invalid. Please ensure it is correctly inputted.',
                        'type': 'bad_api_key'
                    }
                })

                # API Key is not found
                # It was not provided. Construct a response to send back and log the request.
                api_request = APIRequest(
                    authentication_type='NO_AUTH',
                    type=request.method,
                    url=request.get_full_path(),
                    status='401 ERR',
                    ip_address=get_client_ip(request),
                    source=request.META['HTTP_USER_AGENT'],
                    response_to_user=response
                )

                api_request.save()

                return HttpResponse(response, content_type='application/json', status=401)

        else:

            # Create a response
            response = json.dumps({
                'error': {
                    'message': 'API Key not provided. Please provide a relevant API key in the HTTP_AUTHORIZATION header in the username field.',
                    'type': 'no_api_key'
                }
            })

            # It was not provided. Construct a response to send back and log the request.
            api_request = APIRequest(
                authentication_type='NO_AUTH',
                type=request.method,
                url=request.get_full_path(),
                status='401 ERR',
                ip_address=get_client_ip(request),
                source=request.META['HTTP_USER_AGENT'],
                response_to_user=response
            )

            api_request.save()

            return HttpResponse(response, content_type='application/json', status=401)


    def delete(self, request):
        # The first thing we need to do is check to see if the header information has been sent for authorisation etc.
        if 'HTTP_AUTHORIZATION' in request.META:
            # Access GET params: print(request.GET)
            # The key was provided so check it. First we need to base64 decode the key.
            # Extract the key from the string. Base64decode, remove the last colon, and decode to utf-8 rather than bytes
            api_key = base64.b64decode(request.META['HTTP_AUTHORIZATION'].split('Basic ', 1)[1])[:-1].decode(
                'utf-8')

            # Look up API key
            try:
                api_key = APIKey.objects.get(key=api_key)

                # Check to see if the requesters IP is blocked
                ip = get_client_ip(request)

                try:
                    blocked_ip = BlockedIP.objects.get(ip_address=ip)

                    response = json.dumps({
                        'error': {
                            'message': 'Requests from this IP are blocked',
                            'type': 'blocked_ip'
                        }
                    })

                    # This means it does exist so send a return message.
                    api_request = APIRequest(
                        authentication_type='KEY',
                        type=request.method,
                        resource=request.META['HTTP_RESOURCE'],
                        url=request.get_full_path(),
                        status='403 ERR',
                        ip_address=get_client_ip(request),
                        source=request.META['HTTP_USER_AGENT'],
                        api_key=api_key,
                        response_to_user=response
                    )

                    api_request.save()

                    return HttpResponse(response, content_type='application/json', status=403)

                except:
                    # If it doesn't exist then just pass and continue
                    pass

                # API Key is found. No check for a resource.
                if 'HTTP_RESOURCE' in request.META:
                    # Now that we know they provided a resource, let's check to see if it exists.
                    try:
                        resource = Resource.objects.get(
                            name=request.META['HTTP_RESOURCE'],
                            project=api_key.project,
                            request_type=request.method
                        )

                        # Check to see if the resource is "turned off"
                        if not resource.status:
                            response = json.dumps({
                                'error': {
                                    'message': 'The owner of this resource has it disabled/off. Check back later as it may be enabled/turned on',
                                    'type': 'endpoint_off'
                                }
                            })

                            return HttpResponse(response, content_type='application/json')

                        # Now we have the API Key. Let's make sure that the groups match.
                        user_groups = ResourceUserGroup.objects.all().filter(resource=resource)

                        # We only check for user groups if they are present or if the api_key doesn't contain master
                        if user_groups and 'rb_mstr_key_' not in api_key.key:
                            # If the api_key has a user group attached to it
                            # If it doesn't ignore it
                            if api_key.user_group:
                                # Check to see if that user_group is in the set user_groups. If not then say permission denied
                                in_group = False
                                for user_group in user_groups:
                                    if api_key.user_group == user_group.user_group:
                                        in_group = True

                                if in_group is False:
                                    response = json.dumps({
                                        'error': {
                                            'message': 'Permission Denied. Your API Key/User Group doesn\'t allow you to access that resource.',
                                            'type': 'permission_denied'
                                        }
                                    })

                                    # This means a required header is not provided so record it and respond
                                    api_request = APIRequest(
                                        authentication_type='KEY',
                                        type=request.method,
                                        resource=request.META['HTTP_RESOURCE'],
                                        url=request.get_full_path(),
                                        status='403 ERR',
                                        ip_address=get_client_ip(request),
                                        source=request.META['HTTP_USER_AGENT'],
                                        api_key=api_key,
                                        response_to_user=response
                                    )

                                    api_request.save()

                                    return HttpResponse(response, content_type='application/json', status=403)

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
                                if 'HTTP_' + header.key.upper().replace('-', '_') in request.META:
                                    # Does exist.
                                    single_header_object = {
                                        'obj': header,
                                        'provided_value': request.META[
                                            'HTTP_' + header.key.upper().replace('-', '_')]
                                    }

                                    # Append it to the users provided headers
                                    provided_headers.append(single_header_object)
                                else:

                                    response = json.dumps({
                                        'error': {
                                            'message': 'Your request is missing a required header. Missing header is: ' + header.key,
                                            'type': 'missing_header'
                                        }
                                    })

                                    # This means a required header is not provided so record it and respond
                                    api_request = APIRequest(
                                        authentication_type='KEY',
                                        type=request.method,
                                        resource=request.META['HTTP_RESOURCE'],
                                        url=request.get_full_path(),
                                        status='400 ERR',
                                        ip_address=get_client_ip(request),
                                        source=request.META['HTTP_USER_AGENT'],
                                        api_key=api_key,
                                        response_to_user=response
                                    )

                                    api_request.save()

                                    return HttpResponse(response, content_type='application/json',
                                                        status=400)

                        # If we got here we either have a list with no headers or a list with headers that have values.
                        # Either way, if the incorrect values were given we would not be here.
                        resource_request['headers'] = provided_headers

                        # Get the databinds
                        data_binds = ResourceDataBind.objects.all().filter(resource=resource)

                        data_bind_tables = {

                        }

                        if data_binds:
                            full_sql = []

                            # We need to basically loop through each data bind and make it so that they are sorted by table.
                            # This way we can execute multiple INSERTS to different tables.
                            for data_bind in data_binds:

                                # If the table is already listed then just append this data bind.
                                if data_bind.column.table.name in data_bind_tables:
                                    data_bind_tables[data_bind.column.table.name].append(data_bind)
                                else:
                                    data_bind_tables[data_bind.column.table.name] = [data_bind]


                            # We need to loop through each table HOWEVER!!
                            # unlike POST, we don't need to use all elements in the columns as only one should delete
                            # a given row so we use columns[0]
                            try:
                                # So Django doesn't actually support DELETE requests so we need to use URL parameters.
                                for table, columns in data_bind_tables.items():

                                    if columns[0].key not in request.GET:

                                        response = json.dumps({
                                            'error': {
                                                'message': 'Your request is missing a DELETE attribute. Set it as a URL parameter (just like a GET request). Missing attribute is: ' + columns[0].key,
                                                'type': 'missing_attribute'
                                            }
                                        })

                                        # This means a required header is not provided so record it and respond
                                        api_request = APIRequest(
                                            authentication_type='KEY',
                                            type=request.method,
                                            resource=request.META['HTTP_RESOURCE'],
                                            url=request.get_full_path(),
                                            status='400 ERR',
                                            ip_address=get_client_ip(request),
                                            source=request.META['HTTP_USER_AGENT'],
                                            api_key=api_key,
                                            response_to_user=response
                                        )

                                        api_request.save()

                                        return HttpResponse(response, content_type='application/json',
                                                            status=400)
                                    else:
                                        sql = 'DELETE FROM '+table+' WHERE '+columns[0].column.name+'='

                                        if columns[0].type == 'String':
                                            sql += '"'+request.GET[columns[0].key]+'"; '
                                        else:
                                            sql += request.GET[columns[0].key]+'; '

                                        full_sql.append(sql)

                                # Try connect to the server and do database things.
                                try:
                                    database = Database.objects.get(project=resource.project)

                                    conn = db.connect(host=database.server_address, port=3306,
                                                      user=database.user, password=database.password,
                                                      database=database.name, connect_timeout=4)

                                    # Create a cursor
                                    cursor = conn.cursor()

                                    # DELETEs have to be done one after another so do that.
                                    for sql_command in full_sql:
                                        # Now that we have the single query, execute it.
                                        cursor.execute(sql_command)

                                    # Commit the result
                                    conn.commit()

                                    conn.close()

                                    # Cannot connect to the server. Record it and respond
                                    api_request = APIRequest(
                                        authentication_type='KEY',
                                        type=request.method,
                                        resource=request.META['HTTP_RESOURCE'],
                                        url=request.get_full_path(),
                                        status='200 OK',
                                        ip_address=get_client_ip(request),
                                        source=request.META['HTTP_USER_AGENT'],
                                        api_key=api_key
                                    )

                                    api_request.save()

                                    # DO DELETE RESPONSE STUFF
                                    # Check to see if there a response text sources.
                                    resource_text_sources = ResourceTextSource.objects.all().filter(resource=resource)

                                    response = ''

                                    if resource_text_sources:
                                        for resource_text_source in resource_text_sources:
                                            response += resource_text_source.text

                                    # Return it
                                    if resource.response_format == 'JSON':
                                        return HttpResponse(response, content_type='application/json', status=200)


                                except Exception as e:
                                    print(e)
                                    # Create a response
                                    response = json.dumps({
                                        'error': {
                                            'message': 'There was an error with the interaction between us and your database. Please see the error generated by your server below.',
                                            'type': 'database_error',
                                            'database_error': str(e)
                                        }
                                    })

                                    # Cannot connect to the server. Record it and respond
                                    api_request = APIRequest(
                                        authentication_type='KEY',
                                        type=request.method,
                                        resource=request.META['HTTP_RESOURCE'],
                                        url=request.get_full_path(),
                                        status='402 ERR',
                                        ip_address=get_client_ip(request),
                                        source=request.META['HTTP_USER_AGENT'],
                                        api_key=api_key,
                                        response_to_user=response
                                    )

                                    api_request.save()

                                    return HttpResponse(response, content_type='application/json', status=402)

                            except Exception as e:
                                print(e)

                    except Exception as e:

                        # Create a response
                        response = json.dumps({
                            'error': {
                                'message': 'The resource that was requested does not exist.',
                                'type': 'resource_doesnt_exist'
                            }
                        })

                        # Resource does not exist. Record the request.
                        api_request = APIRequest(
                            authentication_type='KEY',
                            type=request.method,
                            resource=request.META['HTTP_RESOURCE'],
                            url=request.get_full_path(),
                            status='404 ERR',
                            ip_address=get_client_ip(request),
                            source=request.META['HTTP_USER_AGENT'],
                            api_key=api_key,
                            response_to_user=response
                        )

                        api_request.save()

                        return HttpResponse(response, content_type='application/json', status=404)
                else:

                    # Create a response
                    response = json.dumps({
                        'error': {
                            'message': 'No resource was provided. Lapis cannot tell what you are trying to access.',
                            'type': 'no_resource_provided'
                        }
                    })

                    # The resource was not provided. Record the requst
                    api_request = APIRequest(
                        authentication_type='KEY',
                        type=request.method,
                        url=request.get_full_path(),
                        status='400 ERR',
                        ip_address=get_client_ip(request),
                        source=request.META['HTTP_USER_AGENT'],
                        api_key=api_key,
                        response_to_user=response
                    )

                    api_request.save()

                    return HttpResponse(response, content_type='application/json', status=400)

            except Exception as e:

                # Create a response
                response = json.dumps({
                    'error': {
                        'message': 'The provided API Key is invalid. Please ensure it is correctly inputted.',
                        'type': 'bad_api_key'
                    }
                })

                # API Key is not found
                # It was not provided. Construct a response to send back and log the request.
                api_request = APIRequest(
                    authentication_type='NO_AUTH',
                    type=request.method,
                    url=request.get_full_path(),
                    status='401 ERR',
                    ip_address=get_client_ip(request),
                    source=request.META['HTTP_USER_AGENT'],
                    response_to_user=response
                )

                api_request.save()

                return HttpResponse(response, content_type='application/json', status=401)

        else:

            # Create a response
            response = json.dumps({
                'error': {
                    'message': 'API Key not provided. Please provide a relevant API key in the HTTP_AUTHORIZATION header in the username field.',
                    'type': 'no_api_key'
                }
            })

            # It was not provided. Construct a response to send back and log the request.
            api_request = APIRequest(
                authentication_type='NO_AUTH',
                type=request.method,
                url=request.get_full_path(),
                status='401 ERR',
                ip_address=get_client_ip(request),
                source=request.META['HTTP_USER_AGENT'],
                response_to_user=response
            )

            api_request.save()

            return HttpResponse(response, content_type='application/json', status=401)

# The main view that handles Public API request. Differs to Private as it requires the project ID as no
# API is required
class RequestHandlerPublic(View):

    # First handle GET requests
    def get(self, request, project_id):
        print(project_id)