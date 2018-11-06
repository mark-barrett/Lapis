<<<<<<< HEAD
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View

from core.forms import *
from core.models import *

=======
from django.shortcuts import render
from django.views import View

>>>>>>> master

class Home(View):

    def get(self, request):
        return render(request, 'core/home.html')


<<<<<<< HEAD
    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        print("Here")

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
            'projects': Project.objects.all().filter(user=request.user)
        }

        return render(request, 'core/create-project.html', context)

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
            return render(request, 'core/create-project.html', context)


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
=======
class Dashboard(View):

    def get(self, request):
        return render(request, 'core/dashboard.html')
>>>>>>> master
