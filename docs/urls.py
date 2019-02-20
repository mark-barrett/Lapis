# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django.conf.urls import url, include

from docs import admin
from docs import views

urlpatterns = [
    url(r'^(?P<project_id>[0-9]+)$', views.GetDocumentation.as_view(), name='get-documentation'),
]