# Developed by Mark Barrett
# http://markbarrettdesign.com
# https://github.com/mark-barrett
import json

from django import template

register = template.Library()

@register.filter(name='to_json')
def to_json(value):
    return json.dumps(value)


@register.simple_tag(name='check_if_project_active_nav')
def check_if_project_active_nav(url, project):
    if '/project/'+str(project.id) in url:
        return "active"