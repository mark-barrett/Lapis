import base64
import json

from django.http import HttpResponse
from django.shortcuts import render
from django.views import View


# The main view that handles Private API requests
from api.models import APIRequest, APIKey
from core.models import Resource, ResourceParameter, ResourceHeader


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
                                    # Does not exist.
                                    print("Exists")
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


                        else:
                            # There are no headers, i.e move on.
                            pass

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