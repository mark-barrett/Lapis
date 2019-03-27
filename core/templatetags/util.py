# Developed by Mark Barrett
# http://markbarrettdesign.com
# https://github.com/mark-barrett
import json

import pycountry
from django import template

register = template.Library()

@register.filter(name='to_json')
def to_json(value):
    return json.dumps(value)


@register.simple_tag(name='check_if_project_active_nav')
def check_if_project_active_nav(url, project):
    if '/project/'+str(project.id) in url:
        return "active"

@register.filter(name='pretty_json')
def pretty_json(input_json):

    parsed = json.loads(input_json)

    return str(json.dumps(parsed, indent=4))


@register.simple_tag(name='last_used_api_key')
def last_used_api_key(api_key):
    from api.models import APIRequest

    api_request = APIRequest.objects.filter(api_key=api_key).order_by('-id')

    if not api_request:
        return 'Not used'
    else:
        return api_request[0].date


@register.simple_tag(name='country_code_to_name')
def country_code_to_name(code):
    return pycountry.countries.get(alpha_2=code).name