# Developed by Mark Barrett
# http://markbarrettdesign.com
# https://github.com/mark-barrett
from django.conf.urls import url, include
from django.views.decorators.csrf import csrf_exempt

from core import admin
from core import views

urlpatterns = [
    url(r'^$', views.Features.as_view(), name='features'),
    url(r'account', views.Account.as_view(), name='account'),
    url(r'learn', views.Learn.as_view(), name='learn'),
    url(r'login', views.Login.as_view(), name='login'),
    url(r'projects', views.Home.as_view(), name='projects'),
    url(r'sign-up', views.SignUp.as_view(), name='sign-up'),
    url(r'logout', views.Logout.as_view(), name='logout'),
    url(r'^dashboard/(?P<project_id>[0-9]+)$', views.DashboardSetSelectedProject.as_view(), name='set-selected-project'),
    url(r'dashboard', views.Dashboard.as_view(), name='dashboard'),
    url(r'^resources', views.Resources.as_view(), name='resources'),
    url(r'^settings/documentation', views.DocumentationSettings.as_view(), name='documentation-settings'),
    url(r'^settings/security', views.ProjectSecuritySettings.as_view(), name='project-security-settings'),
    url(r'^blocked-ip/remove/(?P<ip_id>[0-9]+)$', views.RemoveBlockedIP.as_view(), name='remove-blocked-ip'),
    url(r'^settings', views.ProjectSettings.as_view(), name='project-settings'),
    url(r'^alerts', views.Alerts.as_view(), name='alerts'),
    url(r'^statistics/requests', views.RequestStatistics.as_view(), name='request-statistics'),
    url(r'^statistics', views.ProjectStatistics.as_view(), name='project-statistics'),
    url(r'^api-keys/generate', views.GenerateAPIKey.as_view(), name='generate-api-key'),
    url(r'^api-keys/delete/(?P<id>[-\w]+)$', views.DeleteAPIKey.as_view(), name='delete-api-key'),
    url(r'^api-keys/regenerate/(?P<id>[-\w]+)$', views.RegenerateAPIKey.as_view(), name='regenerate-api-key'),
    url(r'^api-keys', views.APIKeys.as_view(), name='api-keys'),
    url(r'^user-groups/delete/(?P<id>[0-9]+)$', views.DeleteUserGroup.as_view(), name='delete-user-group'),
    url(r'^user-groups/edit/(?P<id>[0-9]+)$', views.EditUserGroup.as_view(), name='edit-user-group'),
    url(r'^user-groups', views.UserGroups.as_view(), name='user-groups'),
    url(r'project/create', views.CreateProject.as_view(), name='create-project'),
    url(r'^project/edit/(?P<project_id>[0-9]+)$', views.EditProject.as_view(), name='edit-project'),
    url(r'^project/delete/(?P<project_id>[0-9]+)$', views.DeleteProject.as_view(), name='delete-project'),
    url(r'^build-database/(?P<project_id>[0-9]+)$', views.BuildDatabase.as_view(), name='build-database'),
    url(r'^resource/reset', views.ResetResource.as_view(), name='reset-resource'),
    url(r'^resource/create', views.CreateResource.as_view(), name='create-resource'),
    url(r'^request/(?P<request_id>[0-9]+)$', views.ViewRequest.as_view(), name='view-request'),
    url(r'^resource/(?P<resource_id>[0-9]+)/requests$', views.ViewResourceRequests.as_view(), name='view-resource-requests'),
    url(r'^resource/view/(?P<resource_id>[0-9]+)$', views.ViewResource.as_view(), name='view-resource'),
    url(r'^resource/edit/(?P<resource_id>[0-9]+)$', views.EditResource.as_view(), name='edit-resource'),
    url(r'^resource/delete/(?P<resource_id>[0-9]+)$', views.DeleteResource.as_view(), name='delete-resource'),
    url(r'^resource/status/(?P<resource_id>[0-9]+)$', views.ChangeResourceStatus.as_view(), name='change-resource-status'),
]
