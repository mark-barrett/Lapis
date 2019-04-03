import json
import operator
import random
import string
from collections import OrderedDict

import redis
from datetime import timedelta, date

from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.gis.geoip import GeoIP
from django.contrib.gis.geoip2 import GeoIP2
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.datetime_safe import datetime
from django.views import View

from api.models import APIKey, APIRequest
from core.forms import *
from core.models import *

from sshtunnel import SSHTunnelForwarder

import MySQLdb as db

from core.tasks import build_database
from docs.models import DocumentationInstance, ProgrammingLanguageChoice


class Features(View):

    def get(self, request):

        return render(request, 'core/features.html')


class Learn(View):

    def get(self, request):

        return render(request, 'core/learn.html')


class Home(View):

    def get(self, request):

        # Check if user is logged in
        if request.user.is_authenticated:

            if 'selected_project_id' in request.session:
                return redirect('/dashboard')
            else:
                context = {
                    'projects': Project.objects.all().filter(user=request.user)
                }

                return render(request, 'core/home.html', context)
        else:
            return redirect('/login')


    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        # Try log the user in
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Hey ' + user.first_name + ', welcome back!')
            return redirect('/dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('/login')


class Login(View):

    def get(self, request):

        return render(request, 'core/login.html')


    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        # Try log the user in
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Hey ' + user.first_name + ', welcome back!')
            return redirect('/projects')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('/login')


class SignUp(View):

    def get(self, request):

        # If the user is already logged in, send them to the dashboard.
        if request.user.is_authenticated:
            if 'selected_project_id' in request.session:
                return redirect('/dashboard')
            else:
                return redirect('/projects')
        else:
            return render(request, 'core/sign-up.html')

    def post(self, request):

        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        # Check if the user exists by email or username
        try:
            user = User.objects.get(username=username)

            messages.error(request, 'User with that username already exists')
            return redirect('/sign-up')
        except:

            try:
                user = User.objects.get(email=email)

                messages.error(request, 'User with that email already exists')
                return redirect('/sign-up')
            except:
                # All okay, let's register the user.
                user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username,
                                                email=email)

                user.set_password(password)

                user.save()

                user = authenticate(username=username, password=password)

                if user is not None:
                    messages.success(request, 'User sign up successful')
                    login(request, user)
                    return redirect('/projects')
                else:
                    messages.error(request, 'Error signing you up')
                    return redirect('/sign-up')


class Logout(View):

    def get(self, request):
        if request.user.is_authenticated:
            # Check if there is a session variable for the project
            if 'selected_project_id' in request.session:
                del request.session['selected_project_id']

            logout(request)
            messages.success(request, "Logged out. Thanks for stopping by!")
            return redirect('/login')


class Dashboard(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        # Check if the project has been selected
        if 'selected_project_id' in request.session:

            # Get today
            today = datetime.today()

            # Get the number of requests this month
            num_requests_this_month = APIRequest.objects.all().filter(date__month=today.month).count()

            # Get the number of requests last month
            num_requests_last_month = APIRequest.objects.all().filter(date__month=today.month-1).count()

            print(num_requests_this_month)
            print(num_requests_last_month)

            # If no requests have been made this month then its a -100% decrease
            if num_requests_this_month == 0:
                percentage = -100
            else:
                # If last months requests are 0 then its a 100% increase
                if num_requests_last_month == 0:
                    percentage = 100
                else:
                    change =  num_requests_this_month - num_requests_last_month

                    percentage = (change / num_requests_last_month) * 100

            project = Project.objects.get(id=request.session['selected_project_id'])

            context = {
                'projects': Project.objects.all().filter(user=request.user),
                'api_keys': APIKey.objects.all(),
                'num_requests_this_month': num_requests_this_month,
                'percentage': percentage,
                'project': project,
                'recent_api_requests': APIRequest.objects.all().filter(api_key__project=project).order_by('-id')[:5],
            }

            return render(request, 'core/dashboard.html', context)
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class DashboardSetSelectedProject(View):

    def get(self, request, project_id):

        # Check if user is logged in
        if request.user.is_authenticated:

            # Check the user has access to this project
            try:
                project = Project.objects.get(id=project_id)

                if project.user == request.user:

                    # Check to see if the project is set as a session.
                    if 'selected_project_id' in request.session:
                        # It already exists
                        # It does exist, check to see if the set value is different to the current.
                        # If it is different set it, if not dont
                        if request.session['selected_project_id'] != project_id:
                            request.session['selected_project_id'] = project_id

                    else:
                        # It does not already exist so set it.
                        request.session['selected_project_id'] = project_id

                        # It does exist, check to see if the set value is different to the current.
                        # If it is different set it, if not dont
                        if request.session['selected_project_id'] != project_id:
                            request.session['selected_project_id'] = project_id
                else:
                    messages.error(request, 'You do not have permission to view that project.')
                    return redirect('/')
            except:
                messages.error(request, 'That project does not exist.')
                return redirect('/')

            # Now return to dashboard
            return redirect('/dashboard')
        else:
            return render(request, 'core/login.html')


class CreateProject(LoginRequiredMixin, View):

    def get(self, request):
        context = {
            'form': ProjectForm(request=request, edit=False),
            'projects': Project.objects.all().filter(user=request.user),
            'action': 'Create'
        }

        return render(request, 'core/create-edit-project.html', context)

    def post(self, request):
        form = ProjectForm(request.POST, request=request)

        if form.is_valid():
            project = form.save(commit=False)

            project.user = request.user

            if 'type' not in request.POST:
                context = {
                    'form': form,
                    'projects': Project.objects.all().filter(user=request.user)
                }

                messages.error(request, 'Please choose a project type.')

                return render(request, 'core/create-edit-project.html', context)
            else:
                project.type = request.POST['type']

            project.save()

            # Create a documentation instance for this project
            documentation_instance = DocumentationInstance(
                project=project
            )

            documentation_instance.save()

            if project.type == 'private':
                # Now that a project has been created lets generate an API key for it.
                api_key_not_found = True

                key = ''

                while api_key_not_found:
                    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))

                    key = 'rb_mstr_key_'+key

                    try:
                        api_key = APIKey.objects.get(key=key)
                    except:
                        api_key_not_found = False

                api_key = APIKey(
                    key=key,
                    user=request.user,
                    project=project
                )

                api_key.save()

                messages.success(request, 'Project and API Key created successfully.')
            else:
                messages.success(request, 'Project created successfully.')

            # Set the id
            request.session['selected_project_id'] = project.id
            return redirect('/dashboard')
        else:
            context = {
                'form': form,
                'projects': Project.objects.all().filter(user=request.user)
            }
            return render(request, 'core/create-edit-project.html', context)


class Resources(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        if 'selected_project_id' in request.session:
            try:
                # Get the project
                project = Project.objects.get(id=request.session['selected_project_id'])

                # Check to make sure the user viewing this project is the owner of it
                if project.user == request.user:
                    context = {
                        'project': project,
                        'projects': Project.objects.all().filter(user=request.user),
                        'resources': Resource.objects.all().filter(project=project)
                    }

                    return render(request, 'core/resources.html', context)
                else:
                    messages.error(request, 'Sorry, we can\'t seem to find what you were looking for.')
                    return redirect('/dashboard')
            except:
                messages.error(request, 'Project does not exist.')
                return redirect('/projects')
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/projects')


class EditProject(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, project_id):

        try:
            # Get the project
            project = Project.objects.get(id=project_id)

            # Check to make sure the user viewing this project is the owner of it
            if project.user == request.user:

                context = {
                    'form': ProjectForm(instance=project, edit=True),
                    'projects': Project.objects.all().filter(user=request.user),
                    'action': 'Edit',
                    'project': project
                }

                return render(request, 'core/create-edit-project.html', context)
            else:
                messages.error(request, 'Sorry, we can\'t seem to find what you were looking for.')
                return redirect('/dashboard')
        except:
            messages.error(request, 'Project does not exist.')
            return redirect('/dashboard')


    def post(self, request, project_id):

        project = Project.objects.get(id=project_id)

        form = ProjectForm(request.POST, instance=project, request=request, project_id=project_id)

        if form.is_valid():
            project = form.save(commit=False)

            project.user = request.user

            if 'type' not in request.POST:
                context = {
                    'form': form,
                    'projects': Project.objects.all().filter(user=request.user)
                }

                messages.error(request, 'Please choose a project type.')

                return render(request, 'core/create-edit-project.html', context)
            else:
                project.type = request.POST['type']

            project.save()

            messages.success(request, 'Project edited successfully.')
            return redirect('/project/' + str(project.id))
        else:
            context = {
                'form': form,
                'projects': Project.objects.all().filter(user=request.user)
            }
            return render(request, 'core/create-edit-project.html', context)


class DeleteProject(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, project_id):
        # Get the project
        project = Project.objects.get(id=project_id)

        # Check the ownership
        if project.user == request.user:
            # Confirmed that they own the project. Delete and redirect to the dashboard with a message.
            project.delete()

            # Remove the session of this project
            del request.session['selected_project_id']
            messages.success(request, 'Successfully deleted project.')
            return redirect('/dashboard')


class BuildDatabase(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, project_id):
        try:
            # Get the project
            project = Project.objects.get(id=project_id)

            # Check to make sure the user viewing this project is the owner of it
            if project.user == request.user:

                context = {
                    'form': DatabaseBuilderForm(),
                    'project_id': project_id,
                    'projects': Project.objects.all().filter(user=request.user)
                }

                return render(request, 'core/build-database.html', context)
            else:
                messages.error(request, 'Sorry, we can\'t seem to find what you were looking for.')
                return redirect('/dashboard')
        except Exception as e:
            print(e)
            messages.error(request, 'Project does not exist.')
            return redirect('/dashboard')

    def post(self, request, project_id):

        try:
            server_address = request.POST['server_address']
            database_name = request.POST['database_name']
            database_user = request.POST['database_user']
            database_password = request.POST['database_password']

            try:
                # Get the project
                project = Project.objects.get(id=project_id)

                # Check to make sure the user viewing this project is the owner of it
                if project.user == request.user:

                    # Now that we have all of the information let us test the SSH Tunnel.
                    # Pass it to Celery to deal with
                    async_result = build_database.delay(project_id=project.id, server_address=server_address,
                                                        database_name=database_name,
                                                        database_user=database_user,
                                                        database_password=database_password)

                    print(async_result)
                    response = {
                        'message': async_result.get()
                    }

                    print(response)

                    return HttpResponse(json.dumps(response), content_type='application/json')

                else:
                    messages.error(request, 'Sorry, we can\'t seem to find what you were looking for.')
                    return redirect('/dashboard')
            except Exception as e:
                print(e)
                messages.error(request, 'Project does not exist.')
                return redirect('/dashboard')

        except Exception as e:

            response = {
                'message': str(e)
            }
            return HttpResponse(json.dumps(response), content_type='application/json')


class CreateResource(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            context = {
                'form': ResourceForm(request=request),
                'project_id': project.id,
                'project': project,
                'user_groups': UserGroup.objects.all().filter(project=project),
                'projects': Project.objects.all().filter(user=request.user)
            }


            database_data = {
                'tables': []
            }

            # Get the database using the project_id
            database = Database.objects.get(project=project)

            # Add the database tables and columns to the context
            tables = DatabaseTable.objects.all().filter(database=database)

            # Loop through all tables
            for table in tables:
                table_obj = {
                    'id': table.id,
                    'name': table.name,
                    'columns': []
                }

                columns = DatabaseColumn.objects.all().filter(table=table)

                # Loop through all columns
                for column in columns:
                    column_obj = {
                        'id': column.id,
                        'name': column.name,
                        'type': column.type
                    }

                    # Append it
                    table_obj['columns'].append(column_obj)

                # Append the table to the database_data
                database_data['tables'].append(table_obj)

            context['database_data'] = json.dumps(database_data)

            return render(request, 'core/create-resource.html', context)

        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


    def post(self, request):
        form = ResourceForm(request.POST, request=request)

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            # If this is the first step i.e the request
            if 'resource' not in request.session:
                if form.is_valid():
                    # Get the values from the form, set it to a session and send back to the same page
                    resource = {
                        'project': project.id,
                        'name': form.cleaned_data['name'],
                        'description': form.cleaned_data['description'],
                        'user_groups': [],
                        'request': {
                            'type': form.cleaned_data['request_type'],
                            'headers': [],
                            'parameters': [],
                            'data_bind_columns': [],
                            'delete_data_bind_columns': []
                        },
                        'response': {}
                    }

                    # Check for user groups
                    if 'user_groups' in request.POST:
                        # They are present so add them
                        for id in request.POST.getlist('user_groups'):
                            resource['user_groups'].append(id)

                    # Get the headers as lists
                    header_keys = request.POST.getlist('header-key')
                    header_value = request.POST.getlist('header-value')
                    header_description = request.POST.getlist('header-description')

                    # Loop through the keys and add the headers to the resource object.
                    for index, key in enumerate(header_keys):
                        header = {
                            'key': key,
                            'value': header_value[index],
                            'description': header_description[index]
                        }

                        resource['request']['headers'].append(header)

                    # Get the parameters as lists if its a GET request
                    if resource['request']['type'] == 'GET':
                        parameter_types = request.POST.getlist('parameter-type')
                        parameter_keys = request.POST.getlist('parameter-key')

                        # Loop through them and add them to the resource
                        for index, key in enumerate(parameter_keys):
                            parameter = {
                                'type': parameter_types[index],
                                'key': key
                            }

                            resource['request']['parameters'].append(parameter)

                    # Get the data binds if a POST request
                    elif resource['request']['type'] == 'POST':
                        data_bind_columns = request.POST.getlist('data-bind-column')
                        data_bind_keys = request.POST.getlist('data-bind-key')
                        data_bind_types = request.POST.getlist('data-bind-type')
                        data_bind_descriptions = request.POST.getlist('data-bind-description')

                        for index, key in enumerate(data_bind_keys):
                            data_bind_column = {
                                'column': data_bind_columns[index],
                                'key': key,
                                'type': data_bind_types[index],
                                'description': data_bind_descriptions[index]
                            }

                            resource['request']['data_bind_columns'].append(data_bind_column)

                    # Get the data binds if a DELETE request
                    elif resource['request']['type'] == 'DELETE':
                        data_bind_columns = request.POST.getlist('delete-data-bind-column')
                        data_bind_keys = request.POST.getlist('delete-data-bind-key')
                        data_bind_types = request.POST.getlist('delete-data-bind-type')
                        data_bind_descriptions = request.POST.getlist('delete-data-bind-description')

                        for index, key in enumerate(data_bind_keys):
                            data_bind_column = {
                                'column': data_bind_columns[index],
                                'key': key,
                                'type': data_bind_types[index],
                                'description': data_bind_descriptions[index]
                            }

                            resource['request']['delete_data_bind_columns'].append(data_bind_column)

                    # Set this as a session variable.
                    request.session['resource'] = resource

                    # Now that the session is set, redirect back to create an resource to create the response
                    return redirect('/resource/create')
            # If we are on the second step, i.e the response
            else:
                # JSON or XML
                response_type = request.POST['response_type']

                # The names of the tables which will be returned as ids
                tables = request.POST.getlist('table')

                # Get the columns that are to be returned
                columns = request.POST.getlist('chosen-column')

                # Try to get the text data sources
                text_data_sources = request.POST.getlist('text-source-hidden-field')

                # Start to construct the response object
                response = {
                    'response_type': response_type,
                    'tables': [],
                    'columns': [],
                }

                # Add the tables to the response object
                for table in tables:
                    response['tables'].append(table)

                # Loop through the tables one by one
                for column in columns:

                    # Create the column object for the response object
                    column_obj = {
                        'column': column,
                        'filters': [],
                        'parent_child_relationships': None
                    }

                    # We need to check and see if there is a filter that exists for this column
                    if 'filter_by_select_'+column in request.POST:
                        # There is a filter column so we need to get that information
                        filter_this_column_by = request.POST.getlist('filter_by_select_'+column)

                        for filter in filter_this_column_by:
                            # Now we have the list of all of the filter items.
                            # They are split by a colon, so split
                            splitted_filter = filter.split(':')

                            # Define the filter
                            filter_obj = {
                                'param_type': splitted_filter[0],
                                'key': splitted_filter[1]
                            }

                            # Append that filter
                            column_obj['filters'].append(filter_obj)

                    # We need to check and see if there are any parents added
                    if 'parent_select_'+column in request.POST:
                        # The parent select does exist.
                        parent_child = request.POST['parent_select_'+column]

                        # Now split it. The first value is the parent column, the second is the parentTable
                        splitted_parent_child = parent_child.split(':')

                        # Define the relationship
                        parent_child = {
                            'parent_column': splitted_parent_child[0],
                            'parent_table': splitted_parent_child[1],
                            'child_column': column,
                            'child_table': DatabaseTable.objects.get(id=int(splitted_parent_child[2])).name
                        }

                        column_obj['parent_child_relationships'] = parent_child

                    # Append that column
                    response['columns'].append(column_obj)

                # Now add the response to the session
                request.session['resource']['response'] = response

                # Now we have created the resource object, now lets start building it.
                try:

                    resource = Resource(
                        name=request.session['resource']['name'],
                        description=request.session['resource']['description'],
                        request_type=request.session['resource']['request']['type'],
                        response_format=request.session['resource']['response']['response_type'],
                        project=project
                    )

                    resource.save()

                    # Check for text data source
                    if text_data_sources:
                        for text_data_source in text_data_sources:
                            text_data_source_obj = ResourceTextSource(
                                text=text_data_source,
                                resource=resource
                            )

                            text_data_source_obj.save()

                    # Check for user groups
                    if request.session['resource']['user_groups']:

                        for user_group_id in request.session['resource']['user_groups']:
                            print(user_group_id)
                            # There are values so make them
                            resource_user_group = ResourceUserGroup(
                                resource=resource,
                                user_group=UserGroup.objects.get(id=user_group_id)
                            )

                            resource_user_group.save()

                    # We need to save all of the headers first
                    for header in request.session['resource']['request']['headers']:
                        resource_header = ResourceHeader(
                            key=header['key'],
                            value=header['value'],
                            description=header['description'],
                            resource=resource
                        )

                        resource_header.save()

                    # If it's a GET request then look for parameters.
                    if request.session['resource']['request']['type'] == 'GET':
                        # We need to save all the sent in parameters first.
                        for parameter in request.session['resource']['request']['parameters']:
                            resource_parameter = ResourceParameter(
                                key=parameter['key'],
                                type=parameter['type'],
                                resource=resource
                            )

                            resource_parameter.save()
                    # If its a POST request look for data binds.
                    elif request.session['resource']['request']['type'] == 'POST':
                        for data_bind in request.session['resource']['request']['data_bind_columns']:
                            data_bind = ResourceDataBind(
                                column=DatabaseColumn.objects.get(id=int(data_bind['column'])),
                                key=data_bind['key'],
                                type=data_bind['type'],
                                description=data_bind['description'],
                                resource=resource
                            )

                            data_bind.save()

                    # If its a DELETE request look for data binds
                    elif request.session['resource']['request']['type'] == 'DELETE':
                        for data_bind in request.session['resource']['request']['delete_data_bind_columns']:
                            data_bind = ResourceDataBind(
                                column=DatabaseColumn.objects.get(id=int(data_bind['column'])),
                                key=data_bind['key'],
                                type=data_bind['type'],
                                description=data_bind['description'],
                                resource=resource
                            )

                            data_bind.save()


                    # Now we have to loop through each column that is to be returned in the response and add it to the database
                    for column in request.session['resource']['response']['columns']:
                        # These are the columns that need to be returned
                        resource_data_source_column = ResourceDataSourceColumn(
                            column_id=column['column'],
                            resource=resource
                        )

                        resource_data_source_column.save()

                        # Check to see if this column has any filters. If it does then add them
                        if column['filters']:
                            for filter in column['filters']:
                                if filter['param_type'] == 'COLUMN':
                                    # Try and lookup that parameter from columns that exist from the Database
                                    column_parameter = DatabaseColumn.objects.get(
                                        id=int(filter['key'])
                                    )

                                    # It's a Column filter
                                    resource_data_source_filter = ResourceDataSourceFilter(
                                        type=filter['param_type'],
                                        column_parameter=column_parameter,
                                        resource=resource
                                    )
                                else:
                                    # Try and lookup that parameter
                                    resource_parameter = ResourceParameter.objects.get(
                                        key=filter['key'],
                                        type=filter['param_type'],
                                        resource=resource
                                    )

                                    resource_data_source_filter = ResourceDataSourceFilter(
                                        type=filter['param_type'],
                                        request_parameter=resource_parameter,
                                        resource=resource
                                    )

                                resource_data_source_filter.save()

                        if column['parent_child_relationships']:
                            # Get the database using project
                            database = Database.objects.get(project=project)

                            # Now that we have it we need to create an instance of ResourceParentChildRelationship
                            parent_child_relationship = ResourceParentChildRelationship(
                                parent_table=DatabaseTable.objects.get(name=column['parent_child_relationships']['parent_table'], database=database),
                                child_table=DatabaseTable.objects.get(name=column['parent_child_relationships']['child_table'], database=database),
                                parent_table_column=DatabaseColumn.objects.get(id=int(column['parent_child_relationships']['parent_column'])),
                                child_table_column=DatabaseColumn.objects.get(id=int(column['parent_child_relationships']['child_column'])),
                                resource=resource
                            )

                            parent_child_relationship.save()

                    messages.success(request, 'Resource successfully created.')

                    del request.session['resource']

                except Exception as e:
                    messages.error(request, str(e))

                return redirect('/resources')
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


class ViewResource(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, resource_id):

        if 'selected_project_id' in request.session:

            try:
                # Get the project
                project = Project.objects.get(id=request.session['selected_project_id'])
                # And the resource
                resource = Resource.objects.get(id=resource_id)

                tables_obj = {}

                # Get the database
                database = Database.objects.get(project=project)

                # Get all of the columns and their tables etc
                resource_column_returns = ResourceDataSourceColumn.objects.all().filter(resource=resource)

                for column in resource_column_returns:
                    db_column = DatabaseColumn.objects.get(id=column.column_id)

                    # Check if this is already in the object
                    if db_column.table.name in tables_obj:
                        # Check if the list exists
                        if tables_obj[db_column.table.name]:
                            tables_obj[db_column.table.name].append(db_column)
                        else:
                            tables_obj[db_column.table.name] = [db_column]
                    # Its not
                    else:
                        # Create it
                        tables_obj[db_column.table.name] = [db_column]


                # Create structure
                response_structure = {}

                # Now lets look for the parent child relationships
                parent_child_relationships = ResourceParentChildRelationship.objects.all().filter(resource=resource)

                for column in resource_column_returns:
                    db_column = DatabaseColumn.objects.get(id=column.column_id)

                    # Loop through the relationships
                    for relationship in parent_child_relationships:
                        # Check if this column is a parent
                        if relationship.parent_table_column == db_column:
                            # Add it nestedly to the response structure
                            column_obj = {relationship.child_table.name: response_structure[relationship.child_table.name]}
                            # Delete the structure that already exists.
                            del response_structure[relationship.child_table.name]

                            # Check if already exists
                            if db_column.table.name in response_structure:
                                # Check if value already in that table section
                                if column_obj not in response_structure[db_column.table.name]:
                                    response_structure[db_column.table.name].append(column_obj)
                            else:
                                # If it doesn't create the list
                                response_structure[db_column.table.name] = [column_obj]
                        else:
                            # If not in a relationship simply display it as it's column name and type.
                            column_obj = {db_column.name: db_column.type}

                            # Check if already exists
                            if db_column.table.name in response_structure:
                                # If it already exists then don't add it.
                                if column_obj not in response_structure[db_column.table.name]:
                                    response_structure[db_column.table.name].append(column_obj)
                            else:
                                # If it doesn't create the list
                                response_structure[db_column.table.name] = [column_obj]


                # Check to make sure the user viewing this project is the owner of it
                if resource.project.user == request.user:


                    context = {
                        'projects': Project.objects.all().filter(user=request.user),
                        'project': project,
                        'resource': resource,
                        'resource_headers': ResourceHeader.objects.all().filter(resource=resource),
                        'resource_parameters': ResourceParameter.objects.all().filter(resource=resource),
                        'resource_column_returns': tables_obj,
                        'resources': Resource.objects.all().filter(project=project),
                        'response_structure': json.dumps(response_structure, sort_keys=True, indent=2),
                        'data_binds': ResourceDataBind.objects.all().filter(resource=resource),
                    }

                    return render(request, 'core/view-resource.html', context)
                else:
                    messages.error(request, 'Sorry, we can\'t seem to find what you were looking for.')
                    return redirect('/dashboard')
            except Exception as e:
                print(e)
                messages.error(request, 'Resource does not exist.')
                return redirect('/dashboard')
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class EditResource(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, resource_id):

        if 'selected_project_id' in request.session:

            resource = Resource.objects.get(id=resource_id)

            # Check the user who is trying to access this resource has the right to/owns it
            if resource.project.user == request.user:

                try:
                    database_tables_obj = {}

                    # Get the database tables
                    database_tables = DatabaseTable.objects.all().filter(database__project=resource.project)

                    for database_table in database_tables:
                        database_tables_obj[database_table.name] = DatabaseColumn.objects.all().filter(table=database_table)

                    print(database_tables_obj)

                    context = {
                        'resource': resource,
                        'headers': ResourceHeader.objects.all().filter(resource=resource),
                        'projects': Project.objects.all().filter(user=request.user),
                        'project': Project.objects.get(id=request.session['selected_project_id']),
                        'database_tables_obj': database_tables_obj
                    }

                    # Get database data
                    database_data = {
                        'tables': []
                    }

                    # Get the database using the project_id
                    database = Database.objects.get(project=resource.project)

                    # Add the database tables and columns to the context
                    tables = DatabaseTable.objects.all().filter(database=database)

                    # Loop through all tables
                    for table in tables:
                        table_obj = {
                            'id': table.id,
                            'name': table.name,
                            'columns': []
                        }

                        columns = DatabaseColumn.objects.all().filter(table=table)

                        # Loop through all columns
                        for column in columns:
                            column_obj = {
                                'id': column.id,
                                'name': column.name,
                                'type': column.type
                            }

                            # Append it
                            table_obj['columns'].append(column_obj)

                        # Append the table to the database_data
                        database_data['tables'].append(table_obj)

                    context['database_data'] = json.dumps(database_data)

                    # GET request is the only one that has parameters
                    if resource.request_type == 'GET':
                        context['parameters'] = ResourceParameter.objects.all().filter(resource=resource)

                    # POST request is the only one that has POST databinds
                    if resource.request_type == 'POST':
                        context['post_data_binds'] = ResourceDataBind.objects.all().filter(resource=resource)

                    # DELETE request is the only one that has DELETE databinds
                    if resource.request_type == 'DELETE':
                        context['delete_data_binds'] = ResourceDataBind.objects.all().filter(resource=resource)

                    return render(request, 'core/edit-resource.html', context)
                except Exception as e:
                    print(e)
                    messages.error(request, 'Error getting that resource.')
                    return redirect('/resources')
            else:
                messages.error(request, 'What your looking for cannot be found.')
                return redirect('/dashboard')
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/projects')

    def post(self, request, resource_id):

        if 'selected_project_id' in request.session:
            resource = Resource.objects.get(id=resource_id)

            # Make sure the person logged in owns the resource
            if resource.project.user == request.user:
                # Check to see if we are on step 2
                if 'resource' not in request.session:

                    try:
                        resource = {
                            'project': resource.project.id,
                            'name': request.POST['name'],
                            'description': request.POST['description'],
                            'request': {
                                'type': request.POST['request_type'],
                                'headers': [],
                                'parameters': [],
                                'data_bind_columns': [],
                                'delete_data_bind_columns': []
                            },
                            'response': {}
                        }

                        # Get the headers as lists
                        header_keys = request.POST.getlist('header-key')
                        header_value = request.POST.getlist('header-value')
                        header_description = request.POST.getlist('header-description')

                        # Loop through the keys and add the headers to the resource object.
                        for index, key in enumerate(header_keys):
                            header = {
                                'key': key,
                                'value': header_value[index],
                                'description': header_description[index]
                            }

                            resource['request']['headers'].append(header)

                            # Get the parameters as lists if its a GET request
                            if resource['request']['type'] == 'GET':
                                parameter_types = request.POST.getlist('parameter-type')
                                parameter_keys = request.POST.getlist('parameter-key')

                                # Loop through them and add them to the resource
                                for index, key in enumerate(parameter_keys):
                                    parameter = {
                                        'type': parameter_types[index],
                                        'key': key
                                    }

                                    resource['request']['parameters'].append(parameter)

                            # Get the data binds if a POST request
                            elif resource['request']['type'] == 'POST':
                                data_bind_columns = request.POST.getlist('data-bind-column')
                                data_bind_keys = request.POST.getlist('data-bind-key')
                                data_bind_types = request.POST.getlist('data-bind-type')
                                data_bind_descriptions = request.POST.getlist('data-bind-description')

                                for index, key in enumerate(data_bind_keys):
                                    data_bind_column = {
                                        'column': data_bind_columns[index],
                                        'key': key,
                                        'type': data_bind_types[index],
                                        'description': data_bind_descriptions[index]
                                    }

                                    resource['request']['data_bind_columns'].append(data_bind_column)

                            # Get the data binds if a DELETE request
                            elif resource['request']['type'] == 'DELETE':
                                data_bind_columns = request.POST.getlist('delete-data-bind-column')
                                data_bind_keys = request.POST.getlist('delete-data-bind-key')
                                data_bind_types = request.POST.getlist('delete-data-bind-type')
                                data_bind_descriptions = request.POST.getlist('delete-data-bind-description')

                                for index, key in enumerate(data_bind_keys):
                                    data_bind_column = {
                                        'column': data_bind_columns[index],
                                        'key': key,
                                        'type': data_bind_types[index],
                                        'description': data_bind_descriptions[index]
                                    }

                                    resource['request']['delete_data_bind_columns'].append(data_bind_column)

                            # Set this as a session variable.
                            request.session['resource'] = resource

                            # Now that the session is set, redirect back to create an resource to create the response
                            return redirect('/resource/create')

                    except Exception as e:
                        messages.error(request, str(e))
                        return redirect('/resource/edit/'+str(resource.id))
            else:
                messages.error(request, 'What your looking for cannot be found.')
                return redirect('/dashboard')
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/projects')



class ViewResourceRequests(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, resource_id):

        if 'selected_project_id' in request.session:

            try:
                # Get the project
                project = Project.objects.get(id=request.session['selected_project_id'])
                # And the resource
                resource = Resource.objects.get(id=resource_id)

                # Check to make sure the user viewing this project is the owner of it
                if resource.project.user == request.user:

                    print(APIRequest.objects.all().filter(resource=resource.name, type=resource.request_type).order_by('-date'))

                    context = {
                        'projects': Project.objects.all().filter(user=request.user),
                        'project': project,
                        'resource': resource,
                        'api_requests': APIRequest.objects.all().filter(resource=resource.name, type=resource.request_type)
                    }

                    return render(request, 'core/view-resource-requests.html', context)
                else:
                    messages.error(request, 'Sorry, we can\'t seem to find what you were looking for.')
                    return redirect('/dashboard')
            except:
                messages.error(request, 'Resource does not exist.')
                return redirect('/dashboard')
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class ViewRequest(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, request_id):

        if 'selected_project_id' in request.session:

            try:
                # Get the project
                project = Project.objects.get(id=request.session['selected_project_id'])

                # Get the request
                api_request = APIRequest.objects.get(id=request_id)

                g = GeoIP2()

                # If its not a developer request
                if api_request.ip_address != '127.0.0.1':
                    country = g.country(api_request.ip_address)
                else:
                    country = None

                # Check to make sure the user viewing this project is the owner of it
                context = {
                    'projects': Project.objects.all().filter(user=request.user),
                    'project': project,
                    'api_request': api_request,
                    'country': country
                }

                return render(request, 'core/view-request.html', context)
            except Exception as e:
                print(e)
                messages.error(request, 'Resource does not exist.')
                return redirect('/dashboard')

        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class ChangeResourceStatus(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, resource_id):

        if 'selected_project_id' in request.session:

            try:
                # Get the project
                project = Project.objects.get(id=request.session['selected_project_id'])
                # And the resource
                resource = Resource.objects.get(id=resource_id)

                # Check to make sure the user viewing this project is the owner of it
                if resource.project.user == request.user:
                    # Change the status to the opposite of what it is
                    resource.status = not resource.status

                    resource.save()

                    # If it was turned on then say so if off say so
                    if resource.status:
                        status = 'on'
                    else:
                        status = 'off'

                    messages.success(request, 'Resource successfully turned '+status+'.')
                    return redirect('/resource/view/'+str(resource.id))
                else:
                    messages.error(request, 'Sorry, we can\'t seem to find what you were looking for.')
                    return redirect('/dashboard')
            except:
                messages.error(request, 'Resource does not exist.')
                return redirect('/resources')
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class DeleteResource(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, resource_id):

        if 'selected_project_id' in request.session:
            # Get the project
            project = Project.objects.get(id=request.session['selected_project_id'])

            # Get the resource
            resource = Resource.objects.get(id=resource_id)

            # Check the ownership
            if resource.project.user == request.user:
                # Confirmed that they own the project. Delete and redirect to the dashboard with a message.
                resource.delete()

                messages.success(request, 'Successfully deleted resource.')
                return redirect('/resources')
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class Account(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        print("Hello World")

        context = {
            'projects': Project.objects.all().filter(user=request.user)
        }

        return render(request, 'core/account.html', context)


class ProjectSettings(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        if 'selected_project_id' in request.session:
            context = {
                'projects': Project.objects.all().filter(user=request.user),
                'project': Project.objects.get(id=request.session['selected_project_id'])
            }

            return render(request, 'core/project-settings.html', context)
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')

    def post(self, request):
        if 'selected_project_id' in request.session:
            # Check if the user who is logged in has access to this project
            project = Project.objects.get(id=request.session['selected_project_id'])

            if project.user == request.user:

                if 'clear-cache' in request.POST:
                    # Clear the cache
                    r = redis.Redis(host='localhost', port=6379, db=0)

                    r.flushall()
                    messages.success(request, 'Successfully cleared the stored cache.')
                    return redirect('/settings')
                else:
                    if 'cache-select' in request.POST:
                        project.caching_expiry = request.POST['cache-select']

                    # Look for enable/disable caching
                    if 'enable_caching' in request.POST:
                        project.caching = True
                    # Otherwise disable it
                    else:
                        project.caching = False
                        project.caching_expiry = '1'

                    project.save()

                    messages.success(request, 'Settings updated successfully.')
                    return redirect('/settings')
            else:
                messages.error(request, 'What your looking for is not found.')
                return redirect('/')
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')



class ProjectSecuritySettings(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            context = {
                'projects': Project.objects.all().filter(user=request.user),
                'project': project,
                'blocked_ips': BlockedIP.objects.all().filter(project=project)
            }

            return render(request, 'core/project-security-settings.html', context)
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


    def post(self, request):

        if 'selected_project_id' in request.session:

            # Check to make sure the user is allowed to delete this
            project = Project.objects.get(id=request.session['selected_project_id'])

            if project.user == request.user:

                # Get the ip
                try:
                    # Create an IP object
                    db_ip = BlockedIP(
                        ip_address=request.POST['ip_address'],
                        project=project
                    )

                    db_ip.save()

                    messages.success(request, 'IP blocked successfully.')

                except Exception as e:
                    print(e)
                    messages.error(request, 'Cannot block IP. '+str(e))

                return redirect('/settings/security')
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')



class RemoveBlockedIP(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, ip_id):

        if 'selected_project_id' in request.session:

            # Check to make sure the user is allowed to delete this
            project = Project.objects.get(id=request.session['selected_project_id'])

            if project.user == request.user:

                # Get the ip
                try:
                    ip = BlockedIP.objects.get(id=ip_id)

                    ip.delete()

                    messages.success(request, 'IP unblocked/removed from blocked IP list.')
                except:
                    messages.error(request, 'Cannot find that IP address')

                return redirect('/settings/security')
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class DocumentationSettings(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            documentation_instance = DocumentationInstance.objects.get(project=project)

            programming_languages = []

            for programming_language in ProgrammingLanguageChoice.objects.all().filter(documentation_instance=documentation_instance):
                programming_languages.append(programming_language.name)

            context = {
                'projects': Project.objects.all().filter(user=request.user),
                'project': project,
                'documentation_instance': documentation_instance,
                'programming_languages': programming_languages
            }

            return render(request, 'core/documentation-settings.html', context)
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


    def post(self, request):

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            # Get the documentation instance
            documentation_instance = DocumentationInstance.objects.get(project=project)

            # Get the required variables and set them to the Documentation Instance
            # If enable documentation was posted then we want to enable the documentation
            if 'enable_documentation' in request.POST:
                documentation_instance.enabled = True
            # Otherwise disabledit
            else:
                documentation_instance.enabled = False

            if 'introduction_text' in request.POST:
                documentation_instance.introduction_text = request.POST['introduction_text']

            if 'logo' in request.FILES:
                logo = request.FILES['logo']
                fs = FileSystemStorage()
                filename = fs.save(logo.name, logo)
                uploaded_file_url = fs.url(filename)

                documentation_instance.logo = uploaded_file_url

            if 'nav_colour' in request.POST:
                documentation_instance.navbar_colour = request.POST['nav_colour']

            if 'support_email' in request.POST:
                documentation_instance.support_email = request.POST['support_email']

            if 'lang_choice' in request.POST:
                languages = request.POST.getlist('lang_choice')

                # Get all current languages and delete them
                programming_languages = ProgrammingLanguageChoice.objects.all().filter(documentation_instance=documentation_instance)

                for language in programming_languages:
                    language.delete()

                # Loop through languages
                for language in languages:
                    db_language = ProgrammingLanguageChoice(
                        name=language,
                        documentation_instance=documentation_instance
                    )

                    db_language.save()

            # Save the documentation instance
            documentation_instance.save()

            # Redirect
            messages.success(request, 'Documentation changes updated.')
            return redirect('/settings/documentation')
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class ProjectStatistics(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        if 'selected_project_id' in request.session:

            # The first statistic we want to get is the actual total requests over the last 7 days
            requests_over_days = []
            requests_today = []

            # Lets get the number of requests over the last 7 days
            today = datetime.today()

            # Generate all of the information for the chart
            # Check to see if today is the first of the month if it is then the start date is 7 days before today
            if today.day < 7:
                start_date = date(today.year, today.month-1, 30-today.day)
            else:
                start_date = date(today.year, today.month, 30-today.day)

            end_date = date(today.year, today.month, today.day+1)

            for single_date in daterange(start_date, end_date):
                # Now we have the date
                api_requests = APIRequest.objects.all().filter(date__day=single_date.day,
                                                               date__month=single_date.month,
                                                               date__year=single_date.year).count()

                requests_over_days.append({
                    'date': single_date,
                    'requests': api_requests
                })

            # Get the number of requests today
            for x in range(1, today.hour+2):
                api_requests = APIRequest.objects.all().filter(date__day=today.day,
                                                               date__month=today.month,
                                                               date__year=today.year,
                                                               date__hour=x).count()

                requests_today.append({
                    'hour': x,
                    'requests': api_requests
                })

            # Find most popular resource
            resources_list = []

            resources = Resource.objects.all().filter(project=Project.objects.get(id=request.session['selected_project_id']))

            for resource in resources:
                resources_list.append({
                    'resource': resource.name,
                    'type': resource.request_type,
                    'requests': APIRequest.objects.all().filter(resource=resource.name, type=resource.request_type).count()
                })

            # Assume the most popular is the first
            if resources_list:
                most_popular = resources_list[0]

                for resource in resources_list:
                    if resource['requests'] > most_popular['requests']:
                        most_popular = resource
            else:
                most_popular = None

            context = {
                'projects': Project.objects.all().filter(user=request.user),
                'project': Project.objects.get(id=request.session['selected_project_id']),
                'requests_over_days': requests_over_days,
                'requests_today_graph': requests_today,
                'requests_today': APIRequest.objects.all().filter(date__day=today.day,
                                                                  date__month=today.month,
                                                                  date__year=today.year).count(),
                'requests_this_month': APIRequest.objects.all().filter(date__month=today.month).count(),
                'most_popular': most_popular
            }

            return render(request, 'core/project-statistics.html', context)
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class Alerts(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        if 'selected_project_id' in request.session:

            context = {
                'projects': Project.objects.all().filter(user=request.user),
                'project': Project.objects.get(id=request.session['selected_project_id']),
            }

            return render(request, 'core/alerts.html', context)
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class RequestStatistics(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            today = datetime.today()

            request_types = {}
            countries = {}

            g = GeoIP2()

            # Get the number of 400 requests vs 200 requests
            api_requests = APIRequest.objects.all()

            # Loop through each api_request
            for api_request in api_requests:
                # If already in the dictionary then increment
                if api_request.status in request_types:
                    request_types[api_request.status] += 1
                # Else just set it to 1
                else:
                    request_types[api_request.status] = 1

                # If its not from the development environment
                if api_request.ip_address != '127.0.0.1':
                    # Get the country
                    country = g.country(api_request.ip_address)

                    # If it already exists then just increment
                    if country['country_code'] in countries:
                        countries[country['country_code']] += 1
                    else:
                        # If not then set to 1 and add country name
                        countries[country['country_code']] = 1

            countries = dict(OrderedDict(sorted(countries.items(), reverse=True)))
            print(countries)

            context = {
                'projects': Project.objects.all().filter(user=request.user),
                'project': project,
                'resources': Resource.objects.all().filter(project=project),
                'today': str(today.day) + '/' + str(today.month) + '/' + str(today.year),
                'request_types': request_types,
                'countries': countries,
            }

            return render(request, 'core/request-statistics.html', context)

        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


    def post(self, request):

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            # Let's get the values from the form
            resource = Resource.objects.get(id=request.POST['resource'])

            context = {
                'projects': Project.objects.all().filter(user=request.user),
                'project': project,
                'resources': Resource.objects.all().filter(project=project),
                'start_date': request.POST['start_date'],
                'end_date': request.POST['end_date'],
                'resource': resource,
            }


            try:
                start_date = request.POST['start_date']
                end_date = request.POST['end_date']

                days_in_range = []

                # Get days between
                start_date_as_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_as_date = datetime.strptime(end_date, '%Y-%m-%d').date()

                # Get time delta (time between)
                delta = end_date_as_date - start_date_as_date

                api_requests = APIRequest.objects.all().filter(resource=resource.name,
                                                               type=resource.request_type, date__range=(start_date, end_date))
                if not api_requests:
                    context['none_found'] = True
                else:
                    # List for holding requests for each day, loop through each day for labels and to get requests
                    requests_over_days = []
                    for i in range(delta.days + 1):
                        this_date = start_date_as_date + timedelta(i)
                        days_in_range.append(this_date)

                        api_request_count = APIRequest.objects.all().filter(resource=resource.name, type=resource.request_type,
                                                                            date__day=this_date.day,
                                                                            date__month=this_date.month,
                                                                            date__year=this_date.year).count()

                        requests_over_days.append(api_request_count)

                    context['requests_over_days_count'] = requests_over_days

                context['days_in_range'] = days_in_range
                context['api_requests'] = api_requests
            except Exception as e:
                print(e)
                # If there is no start_date or end_date specified
                api_requests = APIRequest.objects.all().filter(resource=resource.name,
                                                               type=resource.request_type)

                context['api_requests'] = api_requests

            messages.success(request, 'Showing requests from '+request.POST['start_date']+' to '+request.POST['end_date'])
            return render(request, 'core/request-statistics.html', context)

        else:
            messages.error(request, 'Please select a project.')
            return redirect('/account')


class APIKeys(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            context = {
                'projects': Project.objects.all().filter(user=request.user),
                'project': project,
                'api_keys': APIKey.objects.all().filter(project=project),
                'user_groups': UserGroup.objects.all().filter(project=project)
            }

            return render(request, 'core/api-keys.html', context)

        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class GenerateAPIKey(LoginRequiredMixin, View):
    login_url = '/'

    def post(self, request):

        if 'selected_project_id' in request.session:
            project = Project.objects.get(id=request.session['selected_project_id'])

            # Try get the user group
            if 'user_group' in request.POST:

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
                        user=request.user,
                        project=project,
                        master=False,
                    )

                    # Check to see if the user group is set to all. If it is ignore
                    if request.POST['user_group'] != 'All' and request.POST['user_group'] != 'all':
                        api_key.user_group = UserGroup.objects.get(id=request.POST['user_group'])

                    api_key.save()

                    messages.success(request, 'API Key successfully generated.')
                    return redirect('/api-keys')
                else:
                    messages.error(request, 'Cannot generate API Key for this project as it is public.')
                    return redirect('/api-keys')
            else:
                messages.error(request, 'A user group must be chosen.')
                return redirect('/api-keys')
        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class DeleteAPIKey(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, id):

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            try:
                api_key = APIKey.objects.get(id=id, project=project)

                # Check if the master key. Prevent deletion of it
                if api_key.master:
                    messages.success(request, 'Cannot delete the master API Key.')
                else:
                    api_key.delete()

                messages.success(request, 'API Key successfully deleted.')
            except:
                messages.error(request, 'API Key does not exist.')

            return redirect('/api-keys')

        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class RegenerateAPIKey(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, id):

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            try:
                api_key = APIKey.objects.get(id=id, project=project)

                # Now that a project has been created lets generate an API key for it.
                api_key_not_found = True

                key = ''

                while api_key_not_found:
                    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))

                    # If it is the master key then use the master key prefix string
                    if api_key.master:
                        key = 'rb_mstr_key_' + key
                    else:
                    # If not use the normal one
                        key = 'rb_nrm_key_' + key

                    try:
                        api_key = APIKey.objects.get(key=key)
                    except:
                        api_key_not_found = False

                api_key.key = key

                api_key.save()

                messages.success(request, 'API Key successfully regenerated. New API Key: '+key)
            except:
                messages.error(request, 'API Key does not exist.')

            return redirect('/api-keys')

        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class ResetResource(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            if 'resource' in request.session:
                del request.session['resource']

            return redirect('/resource/create/'+str(project.id))

        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class UserGroups(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            context = {
                'projects': Project.objects.all().filter(user=request.user),
                'project': project,
                'user_group_form': UserGroupForm(),
                'user_groups': UserGroup.objects.all().filter(project=project)
            }

            return render(request, 'core/user-groups.html', context)

        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')

    def post(self, request):

        # Let's make sure the user is logged in
        if 'selected_project_id' in request.session:

            form = UserGroupForm(request.POST)

            if form.is_valid():
                # Commit says don't send to database. We still want to do things to it
                user_group = form.save(commit=False)

                user_group.project = Project.objects.get(id=request.session['selected_project_id'])

                user_group.save()

                messages.success(request, 'User group added successfully.')
                return redirect('/user-groups')
            else:
                messages.error(request, str(form.errors))
                return redirect('/user-groups')

        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class DeleteUserGroup(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, id):

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            # Try get the user group
            try:
                user_group = UserGroup.objects.get(id=id)

                # Delete it
                user_group.delete()

                messages.success(request, 'User group deleted successfully.')
            except:
                messages.error(request, 'User group does not exist.')

            # Now return
            return redirect('/user-groups')

        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


class EditUserGroup(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, id):

        if 'selected_project_id' in request.session:

            project = Project.objects.get(id=request.session['selected_project_id'])

            # Try get the user group
            try:
                user_group = UserGroup.objects.get(id=id)

                context = {
                    'projects': Project.objects.all().filter(user=request.user),
                    'project': project,
                    'user_group_form': UserGroupForm(instance=user_group, edit=True),
                    'user_groups': UserGroup.objects.all().filter(project=project)
                }

                return render(request, 'core/edit-user-group.html', context)
            except Exception as e:
                print(e)
                messages.error(request, 'User group does not exist.')

            # Now return
            return redirect('/user-groups')

        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')


    def post(self, request, id):

        # Let's make sure the user is logged in
        if 'selected_project_id' in request.session:

            user_group = UserGroup.objects.get(id=id)

            form = UserGroupForm(request.POST, instance=user_group)

            if form.is_valid():
                # Commit says don't send to database. We still want to do things to it
                user_group = form.save(commit=False)

                user_group.project = Project.objects.get(id=request.session['selected_project_id'])

                user_group.save()

                messages.success(request, 'User group edited successfully.')
                return redirect('/user-groups')
            else:
                messages.error(request, str(form.errors))
                return redirect('/user-groups')

        else:
            messages.error(request, 'Please select a project.')
            return redirect('/')