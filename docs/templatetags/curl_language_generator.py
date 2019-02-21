# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django import template

from core.models import ResourceHeader, ResourceParameter

register = template.Library()


@register.simple_tag()
def curl_authentication_example(request):
    return '<pre><code class="powershell">$ curl https://'+request.META["HTTP_HOST"]+'/api \<br/> -u rb_nrm_key_123examplekey:</code></pre>'


@register.simple_tag()
def curl_resource_request_example(request):
    return '<pre><code class="powershell">$ curl https://'+request.META["HTTP_HOST"]+'/api \<br/> -u rb_nrm_key_123examplekey: \<br/> -H \'RESTBroker-Resource: Resource\' </code></pre>'


@register.simple_tag()
def curl_generate_resource(request, resource):
    url = 'https://'+request.META["HTTP_HOST"]+'/api'

    # Get the get parameters
    resource_parameters = ResourceParameter.objects.all().filter(resource=resource)

    if resource_parameters:
        # Append the question mark
        url += '?'

        # Loop through all resource parameters
        for index, parameter in enumerate(resource_parameters):
            # If the index is greater than 0, i.e more than one parameter
            if index > 0:
                url += '&'

            url += parameter.key+'=your_value'

    html_to_return = '<pre><code class="powershell">$ curl '+url+' \<br/> -u rb_nrm_key_123examplekey:'

    # Get the resources headers
    resource_headers = ResourceHeader.objects.all().filter(resource=resource)

    # Add the resource to the request
    html_to_return += ' \<br/> -H \'RESTBroker-Resource: '+resource.name+'\''

    # Check if they exist
    if resource_headers:
        # If they do then loop
        for header in resource_headers:
            html_to_return += ' \<br/> -H \''+header.key+': ExampleValue\''


    html_to_return += '</code></pre>'

    return html_to_return

