import json

from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import View

from core.forms import *
from core.models import *

from sshtunnel import SSHTunnelForwarder

import MySQLdb as db

class Home(View):

    def get(self, request):
        return render(request, 'core/home.html')


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
            return redirect('/')


class SignUp(View):

    def get(self, request):

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
                    return redirect('/dashboard')
                else:
                    messages.error(request, 'Error signing you up')
                    return redirect('/sign-up')


class Logout(View):

    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, "Logged out. Thanks for stopping by!")
            return redirect('/')


class Dashboard(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):

        context = {
            'projects': Project.objects.all().filter(user=request.user)
        }

        return render(request, 'core/dashboard.html', context)


class CreateProject(LoginRequiredMixin, View):

    def get(self, request):
        context = {
            'form': ProjectForm(request=request),
            'projects': Project.objects.all().filter(user=request.user),
            'action': 'Create'
        }

        return render(request, 'core/create-edit-project.html', context)

    def post(self, request):
        form = ProjectForm(request.POST, request=request)
        if form.is_valid():
            project = form.save(commit=False)

            project.user = request.user

            project.save()

            messages.success(request, 'Project created successfully.')
            return redirect('/project/'+str(project.id))
        else:
            context = {
                'form': form,
                'projects': Project.objects.all().filter(user=request.user)
            }
            return render(request, 'core/create-edit-project.html', context)


class ViewProject(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, project_id):

        try:
            # Get the project
            project = Project.objects.get(id=project_id)

            # Check to make sure the user viewing this project is the owner of it
            if project.user == request.user:
                context = {
                    'project': project,
                    'projects': Project.objects.all().filter(user=request.user)
                }

                return render(request, 'core/project.html', context)
            else:
                messages.error(request, 'Sorry, we can\'t seem to find what you were looking for.')
                return redirect('/dashboard')
        except:
            messages.error(request, 'Project does not exist.')
            return redirect('/dashboard')


class EditProject(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request, project_id):

        try:
            # Get the project
            project = Project.objects.get(id=project_id)

            # Check to make sure the user viewing this project is the owner of it
            if project.user == request.user:

                context = {
                    'form': ProjectForm(instance=project),
                    'projects': Project.objects.all().filter(user=request.user),
                    'action': 'Edit'
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


class BuildDatabaseSSH(View):

    def post(self, request):
        try:
            ssh_address = request.POST['ssh_address']
            ssh_user = request.POST['ssh_user']
            ssh_password = request.POST['ssh_password']
            database_name = request.POST['database_name']
            database_user = request.POST['database_user']
            database_password = request.POST['database_password']

            # Now that we have all of the information let us test the SSH Tunnel.
            try:

                with SSHTunnelForwarder(
                    (ssh_address, 22),
                    ssh_username=ssh_user,
                    ssh_password=ssh_password,
                    remote_bind_address=('127.0.0.1', 3306)
                ) as server:
                    try:
                        conn = db.connect(host='localhost', port=server.local_bind_port,
                                      user=database_user, password=database_password,
                                      database=database_name)

                        conn.close()
                    except Exception as e:

                        response = {
                            'message': str(e)
                        }
                        return HttpResponse(json.dumps(response), content_type='application/json')

                server.start()

            except Exception as e:

                response = {
                    'message': str(e)
                }
                return HttpResponse(json.dumps(response), content_type='application/json')

        except Exception as e:

            response = {
                'message': str(e)
            }
            return HttpResponse(json.dumps(response), content_type='application/json')
