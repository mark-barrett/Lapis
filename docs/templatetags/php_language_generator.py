# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django import template

from core.models import ResourceParameter, ResourceHeader, ResourceDataBind

register = template.Library()

@register.simple_tag()
def php_authentication_example(request):
    html_to_return = '<pre><code class="php">'

    html_to_return += '$client = new http\Client;<br/>'
    html_to_return += '$request = new http\Client\Request;<br/><br/>'

    html_to_return += '$request->setRequestUrl("https://'+request.META['HTTP_HOST']+'/api");<br/>'
    html_to_return += '$request->setRequestMethod("GET");<br/><br/>'

    html_to_return += '$request->setHeaders(array(<br/>'
    html_to_return += '&nbsp;&nbsp;"Authorization" => "/* Must be base64 encoded */",<br/>'
    html_to_return += '));<br/><br/>'

    html_to_return += '$client->enqueue($request)->send();<br/>'
    html_to_return += '$response = $client->getResponse();<br/>'

    html_to_return += '</code></pre>'

    return html_to_return


@register.simple_tag()
def php_resource_request_example(request):

    html_to_return = '<pre><code class="php">'

    html_to_return += '$client = new http\Client;<br/>'
    html_to_return += '$request = new http\Client\Request;<br/><br/>'

    html_to_return += '$request->setRequestUrl("https://'+request.META['HTTP_HOST']+'/api");<br/>'
    html_to_return += '$request->setRequestMethod("GET");<br/><br/>'

    html_to_return += '$request->setHeaders(array(<br/>'
    html_to_return += '&nbsp;&nbsp;"Authorization" => "/* Must be base64 encoded */",<br/>'
    html_to_return += '&nbsp;&nbsp;"Resource" => "Resource"<br/>'
    html_to_return += '));<br/><br/>'

    html_to_return += '$client->enqueue($request)->send();<br/>'
    html_to_return += '$response = $client->getResponse();<br/>'

    html_to_return += '</code></pre>'

    return html_to_return


@register.simple_tag()
def php_generate_resource(request, resource):
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

    html_to_return = '<pre><code class="php">'

    html_to_return += '$client = new http\Client;<br/>'
    html_to_return += '$request = new http\Client\Request;<br/><br/>'

    if resource.request_type == 'POST':

        data_binds = ResourceDataBind.objects.all().filter(resource=resource)

        if data_binds:
            html_to_return += '$body = new http\Message\Body;<br/>'
            html_to_return += '$body->addForm(array(<br/>'

            for index, data_bind in enumerate(data_binds):
                html_to_return += '&nbsp;&nbsp;"'+data_bind.key+'" => "yourValue"'

                # Check for the last value. If we aren't there then add a comma
                if index < len(data_binds) - 1:
                    html_to_return += ','

                html_to_return += '<br/>'

        html_to_return += '), NULL);<br/><br/>'


    html_to_return += '$request->setRequestUrl("'+url+'");<br/>'
    html_to_return += '$request->setRequestMethod("'+resource.request_type+'");<br/>'

    if resource.request_type == 'POST':
        html_to_return += '$request->setBody($body);<br/>'

    html_to_return += '<br/>$request->setHeaders(array(<br/>'
    html_to_return += '&nbsp;&nbsp;"Authorization" => "/* Must be base64 encoded */",<br/>'
    html_to_return += '&nbsp;&nbsp;"Resource" => "Resource"'

    if resource.request_type == 'POST':
        html_to_return +=  ',<br/>'
    elif resource.request_type == 'GET':
        html_to_return += '<br/>'

    # Get the resources headers
    resource_headers = ResourceHeader.objects.all().filter(resource=resource)

    # Check for headers
    if resource_headers:
        for header in resource_headers:
            html_to_return += '&nbsp;&nbsp;"' + header.key + '" => "your_value"<br/>'

    elif resource.request_type == 'POST':

        html_to_return += '&nbsp;&nbsp;"Content-Type" => "application/x-www-form-urlencoded"<br/>'

    html_to_return += '));<br/><br/>'

    html_to_return += '$client->enqueue($request)->send();<br/>'
    html_to_return += '$response = $client->getResponse();<br/>'

    html_to_return += '</code></pre>'

    return html_to_return