# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django.conf.urls import url, include
from django.views.decorators.csrf import csrf_exempt

from api import admin
from api import views

urlpatterns = [
    url(r'^$', csrf_exempt(views.RequestHandlerPrivate.as_view()), name='request-handler-private'),
    url(r'^/(?P<project_id>[0-9]+)$', views.RequestHandlerPublic.as_view(), name='request-handler-public'),
]