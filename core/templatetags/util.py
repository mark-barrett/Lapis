# Developed by Mark Barrett
# http://markbarrettdesign.com
# https://github.com/mark-barrett
import json

from django import template

register = template.Library()

@register.filter(name='to_json')
def to_json(value):
    return json.dumps(value)