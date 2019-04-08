# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django.conf.urls import url, include
from django.views.decorators.csrf import csrf_exempt

from metaapi import admin
from metaapi import views

urlpatterns = [
    url(r'api-key/generate', csrf_exempt(views.GenerateAPIKey.as_view()), name='generate-api-key'),
    url(r'demo/profiles', csrf_exempt(views.Profiles.as_view()), name='profiles'),
    url(r'demo/posts', csrf_exempt(views.Posts.as_view()), name='posts'),
    url(r'demo/comments', csrf_exempt(views.Comments.as_view()), name='comments'),
    url(r'api-key/regenerate/(?P<nrm_key>[\w-]+)$', csrf_exempt(views.RegenerateAPIKey.as_view()), name='regenerate-api-key'),
    url(r'api-keys/(?P<master_key>[\w-]+)$', csrf_exempt(views.GetAllAPIKeys.as_view()), name='get-all-api-keys')
]