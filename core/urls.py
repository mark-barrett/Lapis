# Developed by Mark Barrett
# http://markbarrettdesign.com
# https://github.com/mark-barrett
from django.conf.urls import url, include
from django.views.decorators.csrf import csrf_exempt

from core import admin
from core import views

urlpatterns = [
    url(r'^$', views.Home.as_view(), name='home'),
    url(r'sign-up', views.SignUp.as_view(), name='sign-up'),
    url(r'logout', views.Logout.as_view(), name='logout'),
    url(r'dashboard', views.Dashboard.as_view(), name='dashboard'),
    url(r'account', views.Account.as_view(), name='account'),
    url(r'^project/(?P<project_id>[0-9]+)$', views.ViewProject.as_view(), name='view-project'),
    url(r'^project/(?P<project_id>[0-9]+)/settings$', views.ProjectSettings.as_view(), name='project-settings'),
    url(r'^project/(?P<project_id>[0-9]+)/statistics', views.ProjectStatistics.as_view(), name='project-statistics'),
    url(r'^project/(?P<project_id>[0-9]+)/api-keys/generate', views.GenerateAPIKey.as_view(), name='generate-api-key'),
    url(r'^project/(?P<project_id>[0-9]+)/api-keys/delete/(?P<id>[-\w]+)$', views.DeleteAPIKey.as_view(), name='delete-api-key'),
    url(r'^project/(?P<project_id>[0-9]+)/api-keys/regenerate/(?P<id>[-\w]+)$', views.RegenerateAPIKey.as_view(), name='regenerate-api-key'),
    url(r'^project/(?P<project_id>[0-9]+)/api-keys', views.APIKeys.as_view(), name='api-keys'),
    url(r'project/create', views.CreateProject.as_view(), name='create-project'),
    url(r'^project/edit/(?P<project_id>[0-9]+)$', views.EditProject.as_view(), name='edit-project'),
    url(r'^project/delete/(?P<project_id>[0-9]+)$', views.DeleteProject.as_view(), name='delete-project'),
    url(r'^build-database/(?P<project_id>[0-9]+)$', views.BuildDatabase.as_view(), name='build-database'),
    url(r'^resource/reset/(?P<project_id>[0-9]+)$', views.ResetResource.as_view(), name='reset-resource'),
    url(r'^resource/create/(?P<project_id>[0-9]+)$', views.CreateResource.as_view(), name='create-resource'),
    url(r'^project/(?P<project_id>[0-9]+)/request/(?P<request_id>[0-9]+)$', views.ViewRequest.as_view(), name='view-request'),
    url(r'^project/(?P<project_id>[0-9]+)/resource/(?P<resource_id>[0-9]+)/requests$', views.ViewResourceRequests.as_view(), name='view-resource-requests'),
    url(r'^project/(?P<project_id>[0-9]+)/resource/view/(?P<resource_id>[0-9]+)$', views.ViewResource.as_view(), name='view-resource'),
    url(r'^project/(?P<project_id>[0-9]+)/resource/delete/(?P<resource_id>[0-9]+)$', views.DeleteResource.as_view(), name='delete-resource'),
    url(r'^project/(?P<project_id>[0-9]+)/resource/status/(?P<resource_id>[0-9]+)$', views.ChangeResourceStatus.as_view(), name='change-resource-status'),
]
