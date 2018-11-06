from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View


class Home(View):

    def get(self, request):
        return render(request, 'core/home.html')


    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        # Try log the user in
        user = authenticate(username=username, password=password)

        if user is not None:
            messages.success(request, 'Hey ' + user.first_name + ', welcome back!')
            return redirect('/dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('/')


class Dashboard(View):

    def get(self, request):
        return render(request, 'core/dashboard.html')
