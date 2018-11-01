# Developed by Mark Barrett
# http://markbarrettdesign.com
# https://github.com/mark-barrett
from django.conf.urls import url, include

from core import admin
from core import views

urlpatterns = [
    url(r'^$', views.Home.as_view(), name='home'),
    url(r'dashboard', views.Dashboard.as_view(), name='dashboard')
]
