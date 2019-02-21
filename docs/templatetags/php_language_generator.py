# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django import template

from core.models import ResourceParameter, ResourceHeader

register = template.Library()

@register.simple_tag()
def php_authentication_example(request):
    html_to_return = '<pre><code class="php">'

    html_to_return += '$request = new HttpRequest();<br/>'
    html_to_return += '$request->setUrl("https://'+request.META['HTTP_HOST']+'");<br/>'
    html_to_return += '$request->setMethod(HTTP_METH_GET);<br/><br/>'

    html_to_return += '$request->setHeaders(array(<br/>'
    html_to_return += '&nbsp;&nbsp;"Authorization" => "/* Must be base64 encoded */"<br/>'
    html_to_return += '));<br/><br/>'

    html_to_return += 'try {<br/>'
    html_to_return += '&nbsp;&nbsp;$response = $request->send();<br/><br/>'
    html_to_return += '&nbsp;&nbsp;echo $response->getBody();<br/>'
    html_to_return += '} catch (HttpException $ex) {<br/>'
    html_to_return += '&nbsp;&nbsp; echo $ex;<br/>'
    html_to_return += '}'

    html_to_return += '</code></pre>'

    return html_to_return


@register.simple_tag()
def php_resource_request_example(request):
    html_to_return = '<pre><code class="php">'

    html_to_return += '$request = new HttpRequest();<br/>'
    html_to_return += '$request->setUrl("https://'+request.META['HTTP_HOST']+'");<br/>'
    html_to_return += '$request->setMethod(HTTP_METH_GET);<br/><br/>'

    html_to_return += '$request->setHeaders(array(<br/>'
    html_to_return += '&nbsp;&nbsp;"Authorization" => "/* Must be base64 encoded */",<br/>'
    html_to_return += '&nbsp;&nbsp;"RESTBroker-Resource" => "Resource"<br/>'
    html_to_return += '));<br/><br/>'

    html_to_return += 'try {<br/>'
    html_to_return += '&nbsp;&nbsp;$response = $request->send();<br/><br/>'
    html_to_return += '&nbsp;&nbsp;echo $response->getBody();<br/>'
    html_to_return += '} catch (HttpException $ex) {<br/>'
    html_to_return += '&nbsp;&nbsp; echo $ex;<br/>'
    html_to_return += '}'

    html_to_return += '</code></pre>'

    return html_to_return


@register.simple_tag()
def php_generate_resource(request, resource):
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

    html_to_return = '<pre><code class="php">'

    html_to_return += '$request = new HttpRequest();<br/>'
    html_to_return += '$request->setUrl("'+url+'");<br/>'
    html_to_return += '$request->setMethod(HTTP_METH_GET);<br/><br/>'

    html_to_return += '$request->setHeaders(array(<br/>'
    html_to_return += '&nbsp;&nbsp;"Authorization" => "/* Must be base64 encoded */",<br/>'
    html_to_return += '&nbsp;&nbsp;"RESTBroker-Resource" => "Resource"<br/>'

    # Get the resources headers
    resource_headers = ResourceHeader.objects.all().filter(resource=resource)

    # Check for headers
    if resource_headers:
        for header in resource_headers:
            html_to_return += '&nbsp;&nbsp;"'+header.key+'" => "your_value"<br/>'

    html_to_return += '));<br/><br/>'

    html_to_return += 'try {<br/>'
    html_to_return += '&nbsp;&nbsp;$response = $request->send();<br/><br/>'
    html_to_return += '&nbsp;&nbsp;echo $response->getBody();<br/>'
    html_to_return += '} catch (HttpException $ex) {<br/>'
    html_to_return += '&nbsp;&nbsp; echo $ex;<br/>'
    html_to_return += '}'

    html_to_return += '</code></pre>'

    return html_to_return