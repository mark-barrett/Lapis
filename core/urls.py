# Developed by Mark Barrett
# http://markbarrettdesign.com
# https://github.com/mark-barrett
from django.conf.urls import url, include

from core import admin
from core import views

urlpatterns = [
    url(r'^$', views.Home.as_view(), name='home'),
    url(r'sign-up', views.SignUp.as_view(), name='sign-up'),
    url(r'logout', views.Logout.as_view(), name='logout'),
    url(r'dashboard', views.Dashboard.as_view(), name='dashboard'),
    url(r'^project/(?P<project_id>[0-9]+)$', views.ViewProject.as_view(), name='view-project'),
    url(r'project/create', views.CreateProject.as_view(), name='create-project'),
    url(r'^project/edit/(?P<project_id>[0-9]+)$', views.EditProject.as_view(), name='edit-project'),
    url(r'^project/delete/(?P<project_id>[0-9]+)$', views.DeleteProject.as_view(), name='delete-project'),
    url(r'^build-database/(?P<project_id>[0-9]+)$', views.BuildDatabase.as_view(), name='build-database'),
]
