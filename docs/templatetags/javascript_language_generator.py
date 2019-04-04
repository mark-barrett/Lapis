# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django import template

from core.models import ResourceParameter, ResourceHeader, ResourceDataBind

register = template.Library()

@register.simple_tag()
def javascript_authentication_example(request):
    html_to_return = '<pre><code class="javascript">'

    html_to_return += 'var settings = {<br/>'
    html_to_return += '&nbsp;&nbsp; "async": true,<br/>'
    html_to_return += '&nbsp;&nbsp; "crossDomain": true,<br/>'
    html_to_return += '&nbsp;&nbsp; "url": "https://'+request.META['HTTP_HOST']+'/api",<br/>'
    html_to_return += '&nbsp;&nbsp; "method": "GET",<br/>'
    html_to_return += '&nbsp;&nbsp; "headers": {<br/>'
    html_to_return += '&nbsp;&nbsp;&nbsp;&nbsp; "Authorization": /* Your key. Must be base64 encoded */,<br/>'
    html_to_return += '&nbsp;&nbsp;&nbsp;&nbsp; "cache-control": "no-cache"<br/>'
    html_to_return += '&nbsp;&nbsp;}<br/>'
    html_to_return += '}<br/><br/>'

    html_to_return += '$.ajax(settings).done(function(response) {<br/>'
    html_to_return += '&nbsp;&nbsp; /* Use response */<br/>'
    html_to_return += '});<br/>'

    html_to_return += '</code></pre>'

    return html_to_return


@register.simple_tag()
def javascript_resource_request_example(request):
    html_to_return = '<pre><code class="javascript">'

    html_to_return += 'var settings = {<br/>'
    html_to_return += '&nbsp;&nbsp; "async": true,<br/>'
    html_to_return += '&nbsp;&nbsp; "crossDomain": true,<br/>'
    html_to_return += '&nbsp;&nbsp; "url": "https://' + request.META['HTTP_HOST'] + '/api",<br/>'
    html_to_return += '&nbsp;&nbsp; "method": "GET",<br/>'
    html_to_return += '&nbsp;&nbsp; "headers": {<br/>'
    html_to_return += '&nbsp;&nbsp;&nbsp;&nbsp; "Authorization": /* Your key. Must be base64 encoded */,<br/>'
    html_to_return += '&nbsp;&nbsp;&nbsp;&nbsp; "Resource": "Resource",<br/>'
    html_to_return += '&nbsp;&nbsp;&nbsp;&nbsp; "cache-control": "no-cache"<br/>'
    html_to_return += '&nbsp;&nbsp;}<br/>'
    html_to_return += '}<br/><br/>'

    html_to_return += '$.ajax(settings).done(function(response) {<br/>'
    html_to_return += '&nbsp;&nbsp; /* Use response */<br/>'
    html_to_return += '});<br/>'

    html_to_return += '</code></pre>'

    return html_to_return


@register.simple_tag()
def javascript_generate_resource(request, resource):
    url = 'https://lapis.works/api'

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

    html_to_return = '<pre style="height: 450px"><code class="javascript">'

    # If its a POST request then build the form elements for the POST
    if resource.request_type == 'POST':
        html_to_return += 'var form = new FormData();<br/>'

        data_binds = ResourceDataBind.objects.all().filter(resource=resource)

        if data_binds:

            for data_bind in data_binds:
                html_to_return += 'form.append("'+data_bind.key+'", "yourValue");<br/>'

        html_to_return += '<br/>'

    html_to_return += 'var settings = {<br/>'
    html_to_return += '&nbsp;&nbsp; "async": true,<br/>'
    html_to_return += '&nbsp;&nbsp; "crossDomain": true,<br/>'
    html_to_return += '&nbsp;&nbsp; "url": "'+url+'",<br/>'
    html_to_return += '&nbsp;&nbsp; "method": "'+resource.request_type+'",<br/>'
    html_to_return += '&nbsp;&nbsp; "headers": {<br/>'
    html_to_return += '&nbsp;&nbsp;&nbsp;&nbsp; "Authorization": /* Your key. Must be base64 encoded */,<br/>'
    html_to_return += '&nbsp;&nbsp;&nbsp;&nbsp; "Resource": "Resource",<br/>'

    # Get the resources headers
    resource_headers = ResourceHeader.objects.all().filter(resource=resource)

    # Check for headers
    if resource_headers:
        for header in resource_headers:
            html_to_return += '&nbsp;&nbsp;&nbsp;&nbsp; "'+header.key+'": "your_value",<br/>'

    html_to_return += '&nbsp;&nbsp;&nbsp;&nbsp; "cache-control": "no-cache"<br/>'
    html_to_return += '&nbsp;&nbsp;}'

    if resource.request_type == 'GET':
        html_to_return += '<br/>'
    elif resource.request_type == 'POST':
        html_to_return += ',<br/>'
        html_to_return += '&nbsp;&nbsp; "processData": false,<br/>'
        html_to_return += '&nbsp;&nbsp; "contentType": false,<br/>'
        html_to_return += '&nbsp;&nbsp; "mimeType": "multipart/form-data",<br/>'
        html_to_return += '&nbsp;&nbsp; "data": form<br/>'
    html_to_return += '}<br/><br/>'

    html_to_return += '$.ajax(settings).done(function(response) {<br/>'
    html_to_return += '&nbsp;&nbsp; /* Use response */<br/>'
    html_to_return += '});<br/>'

    html_to_return += '</code></pre>'

    return html_to_return