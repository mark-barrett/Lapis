import json
import random
import string

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import View

from api.models import APIKey


class GenerateAPIKey(View):

    def get(self, request):
        return redirect('/')

    def post(self, request):

        try:
            if 'master_key' not in request.POST:
                response = {
                    'message': 'The projects master key must be sent in the master_key field to generate a new API key.'
                }

                return HttpResponse(json.dumps(response), content_type='application/json', status=403)
            else:
                # Try get the API key
                try:
                    mstr_api_key = APIKey.objects.get(key=request.POST['master_key'])

                    # We found it
                    project = mstr_api_key.project

                    # Generate an API key
                    if project.type == 'private':
                        # Now that a project has been created lets generate an API key for it.
                        api_key_not_found = True

                        key = ''

                        while api_key_not_found:
                            key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))

                            key = 'rb_nrm_key_' + key

                            try:
                                api_key = APIKey.objects.get(key=key)
                            except:
                                api_key_not_found = False

                        api_key = APIKey(
                            key=key,
                            user=mstr_api_key.user,
                            project=project,
                            master=False
                        )

                        api_key.save()

                        response = {
                            'api_key': api_key.key,
                            'message': 'Successfully generated API key.'
                        }
                        return HttpResponse(json.dumps(response), content_type='application/json', status=200)

                except Exception as e:
                    print(e)
                    response = {
                        'message': 'Cannot generate key, invalid master key.'
                    }

                    return HttpResponse(json.dumps(response), content_type='application/json', status=403)
        except Exception as e:

            response = {
                'message': e
            }

            return HttpResponse(json.dumps(response), content_type='application/json', status=403)


class RegenerateAPIKey(View):

    def get(self, request):
        return redirect('/')

    def post(self, request, nrm_key):

        try:
            if 'master_key' not in request.POST:
                response = {
                    'message': 'The projects master key must be sent in the master_key field to generate a new API key.'
                }

                return HttpResponse(json.dumps(response), content_type='application/json', status=403)
            else:
                # Try get the API key
                try:
                    mstr_api_key = APIKey.objects.get(key=request.POST['master_key'])

                    project = mstr_api_key.project

                    try:
                        api_key = APIKey.objects.get(key=nrm_key)

                        # Now that a project has been created lets generate an API key for it.
                        api_key_not_found = True

                        key = ''

                        while api_key_not_found:
                            key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))

                            # If not use the normal one
                            key = 'rb_nrm_key_' + key

                            try:
                                other_api_key = APIKey.objects.get(key=key)
                            except:
                                api_key_not_found = False

                        api_key.key = key

                        api_key.save()

                        response = {
                            'api_key': api_key.key,
                            'message': 'Successfully regenerated API Key.'
                        }
                        return HttpResponse(json.dumps(response), content_type='application/json', status=200)
                    except:
                        response = {
                            'message': 'The key you are trying to regenerate does not exist.'
                        }
                        return HttpResponse(json.dumps(response), content_type='application/json', status=403)

                except Exception as e:
                    print(e)
                    response = {
                        'message': 'Cannot generate key, invalid master key.'
                    }

                    return HttpResponse(json.dumps(response), content_type='application/json', status=403)
        except Exception as e:

            response = {
                'message': e
            }

            return HttpResponse(json.dumps(response), content_type='application/json', status=403)


class GetAllAPIKeys(View):

    def get(self, request):
        return redirect('/')

    def post(self, request, master_key):

        # Check that the master key is valid
        try:
            api_key = APIKey.objects.get(key=master_key)

            keys = []

            api_keys_from_project = APIKey.objects.all().filter(project=api_key.project)

            for proj_api_key in api_keys_from_project:
                if 'rb_mstr_key_' not in proj_api_key.key:
                    single_key = {
                        'key': proj_api_key.key,
                        'created_at': str(proj_api_key.created_at),
                    }

                    keys.append(single_key)

            # Return them
            return HttpResponse(json.dumps(keys), content_type='application/json', status=400)

        except Exception as e:
            print(e)
            response = {
                'message': 'Cannot get API keys, invalid master key.'
            }

            return HttpResponse(json.dumps(response), content_type='application/json', status=403)
