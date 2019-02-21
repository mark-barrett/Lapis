# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django import template

register = template.Library()

@register.simple_tag()
def python_authentication_example(request):
    return "<pre><code class='python'>import requests<br/><br/>response = requests.get('https://"+request.META['HTTP_HOST']+"/api', auth=('rb_nrm_key_examplekey', ''))</code></pre>"

