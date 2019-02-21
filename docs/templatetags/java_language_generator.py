# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django import template

from core.models import ResourceParameter, ResourceHeader

register = template.Library()

@register.simple_tag()
def java_authentication_example(request):
    html_to_return = '<pre><code class="java">'

    html_to_return += 'OkHttpClient client = new OkHttpClient();<br/><br/>'

    html_to_return += '/* Create an Basic key using the API key */'

    html_to_return += '<br/>String credential = Credentials.basic("rb_nrm_key_examplekey", "");<br/><br/>'

    html_to_return += 'Request request = new Request.Builder()<br/>'

    html_to_return += '.url("https://'+request.META["HTTP_HOST"]+'/api")<br/>'

    html_to_return += '.get()<br/>'

    html_to_return += '.addHeader("Authorization", credential)<br/>'

    html_to_return += '.build();<br/><br/>'

    html_to_return += 'Response response = client.newCall(request).execute();'

    html_to_return += '</code></pre>'

    return html_to_return


@register.simple_tag()
def java_resource_request_example(request):
    html_to_return = '<pre><code class="java">'

    html_to_return += 'OkHttpClient client = new OkHttpClient();<br/><br/>'

    html_to_return += '/* Create an Basic key using the API key */'

    html_to_return += '<br/>String credential = Credentials.basic("rb_nrm_key_examplekey", "");<br/><br/>'

    html_to_return += 'Request request = new Request.Builder()<br/>'

    html_to_return += '.url("https://' + request.META["HTTP_HOST"] + '/api")<br/>'

    html_to_return += '.get()<br/>'

    html_to_return += '.addHeader("Authorization", credential)<br/>'

    html_to_return += '.addHeader("RESTBroker-Resource", "Resource")<br/>'

    html_to_return += '.build();<br/><br/>'

    html_to_return += 'Response response = client.newCall(request).execute();'

    html_to_return += '</code></pre>'

    return html_to_return


@register.simple_tag()
def java_generate_resource(request, resource):
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

    html_to_return = '<pre><code class="java">'

    html_to_return += 'OkHttpClient client = new OkHttpClient();<br/><br/>'

    html_to_return += '/* Create an Basic key using the API key */'

    html_to_return += '<br/>String credential = Credentials.basic("rb_nrm_key_examplekey", "");<br/><br/>'

    html_to_return += 'Request request = new Request.Builder()<br/>'

    html_to_return += '.url("'+url+'")<br/>'

    html_to_return += '.get()<br/>'

    html_to_return += '.addHeader("Authorization", credential)<br/>'

    html_to_return += '.addHeader("RESTBroker-Resource", "Resource")<br/>'

    # Get the resources headers
    resource_headers = ResourceHeader.objects.all().filter(resource=resource)

    # Check for headers
    if resource_headers:
        for header in resource_headers:
            html_to_return += '.addHeader("'+header.key+'", "your_value")<br/>'

    html_to_return += '.build();<br/><br/>'

    html_to_return += 'Response response = client.newCall(request).execute();'

    html_to_return += '</code></pre>'

    return html_to_return