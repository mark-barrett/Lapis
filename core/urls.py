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
    url(r'^project/(?P<project_id>[0-9]+)/api-keys/generate', views.GenerateAPIKey.as_view(), name='generate-api-key'),
    url(r'^project/(?P<project_id>[0-9]+)/api-keys/delete/(?P<id>[-\w]+)$', views.DeleteAPIKey.as_view(), name='delete-api-key'),
    url(r'^project/(?P<project_id>[0-9]+)/api-keys/regenerate/(?P<id>[-\w]+)$', views.RegenerateAPIKey.as_view(), name='regenerate-api-key'),
    url(r'^project/(?P<project_id>[0-9]+)/api-keys', views.APIKeys.as_view(), name='api-keys'),
    url(r'project/create', views.CreateProject.as_view(), name='create-project'),
    url(r'^project/edit/(?P<project_id>[0-9]+)$', views.EditProject.as_view(), name='edit-project'),
    url(r'^project/delete/(?P<project_id>[0-9]+)$', views.DeleteProject.as_view(), name='delete-project'),
    url(r'^build-database/(?P<project_id>[0-9]+)$', views.BuildDatabase.as_view(), name='build-database'),
    url(r'^endpoint/reset/(?P<project_id>[0-9]+)$', views.ResetEndpoint.as_view(), name='reset-endpoint'),
    url(r'^endpoint/create/(?P<project_id>[0-9]+)$', views.CreateEndpoint.as_view(), name='create-endpoint'),
    url(r'^project/(?P<project_id>[0-9]+)/endpoint/view/(?P<endpoint_id>[0-9]+)$', views.ViewEndpoint.as_view(), name='view-endpoint'),
    url(r'^project/(?P<project_id>[0-9]+)/endpoint/delete/(?P<endpoint_id>[0-9]+)$', views.DeleteEndpoint.as_view(), name='delete-endpoint'),
    url(r'^project/(?P<project_id>[0-9]+)/endpoint/status/(?P<endpoint_id>[0-9]+)$', views.ChangeEndpointStatus.as_view(), name='change-endpoint-status'),
]
