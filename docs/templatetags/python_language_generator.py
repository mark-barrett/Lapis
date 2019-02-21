# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django import template

from core.models import ResourceParameter, ResourceHeader

register = template.Library()

@register.simple_tag()
def python_authentication_example(request):
    return "<pre><code class='python'>import requests<br/><br/>response = requests.get('https://"+request.META['HTTP_HOST']+"/api'," \
            "<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; auth=('rb_nrm_key_examplekey', ''))</code></pre>"

@register.simple_tag()
def python_resource_request_example(request):
    return "<pre><code class='python'>import requests<br/><br/>headers = {'RESTBroker-Resource': 'Resource'}<br/><br/>response = "\
            "requests.get('https://"+request.META['HTTP_HOST']+"/api',<br/> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"\
            "&nbsp;&nbsp;&nbsp; auth=('rb_nrm_key_examplekey', ''), <br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; headers=headers)</code></pre>"


@register.simple_tag()
def python_generate_resource(request, resource):
    url = 'https://' + request.META["HTTP_HOST"] + '/api'

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

            url += parameter.key + '=your_value'

    html_to_return = '<pre><code class="python">import requests<br/><br/>'

    # Get the headers
    resource_headers = ResourceHeader.objects.all().filter(resource=resource)

    # Check if there are headers
    if resource_headers:

        # Add the Resource header
        html_to_return += 'headers = {<br/>&nbsp;&nbsp;\'RESTBroker-Resource\': \'' + resource.name + '\','

        for index, header in enumerate(resource_headers):
            html_to_return += '<br/>&nbsp;&nbsp;\''+header.key+'\': your_value'

            # Check for the last value. If we aren't there then add a comma
            if index < len(resource_headers)-1:
                html_to_return += ','

        # Add the last bracket
        html_to_return += '<br/>}'
    else:
        html_to_return += 'headers = {\'RESTBroker-Resource\': \'' + resource.name + '\'}'

    # Now do the request part
    html_to_return += "<br/><br/>response = requests.get('"+url+"',<br/> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" \
                        "&nbsp;&nbsp;&nbsp; auth=('rb_nrm_key_examplekey', ''), <br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; headers=headers)</code></pre>"

    html_to_return += '</code></pre>'

    return html_to_return
