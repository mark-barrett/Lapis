# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django.conf.urls import url, include
from django.views.decorators.csrf import csrf_exempt

from metaapi import admin
from metaapi import views

urlpatterns = [
    url(r'api-key/generate', csrf_exempt(views.GenerateAPIKey.as_view()), name='generate-api-key'),
    url(r'api-key/regenerate/(?P<nrm_key>[\w-]+)$', csrf_exempt(views.RegenerateAPIKey.as_view()), name='regenerate-api-key'),
    url(r'api-keys/(?P<master_key>[\w-]+)$', csrf_exempt(views.GetAllAPIKeys.as_view()), name='get-all-api-keys')
]