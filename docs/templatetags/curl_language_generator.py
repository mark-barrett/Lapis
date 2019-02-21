# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django import template

register = template.Library()

@register.simple_tag()
def curl_authentication_example(request):
    return '<pre><code class="powershell">$ curl https://'+request.META["HTTP_HOST"]+'/api \<br/> -u rb_nrm_key_123examplekey</code></pre>'

