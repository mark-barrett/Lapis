# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django import template

from core.models import ResourceParameter, ResourceHeader, ResourceDataBind

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

    if resource.request_type == 'POST':
        html_to_return += 'RequestBody requestBody = new MultipartBody.Builder()<br/>'

        html_to_return += '.setType(MultipartBody.FORM)<br/>'

        # Get the data binds
        data_binds = ResourceDataBind.objects.all().filter(resource=resource)

        if data_binds:
            for data_bind in data_binds:
                html_to_return += '.addFormDataPart("'+data_bind.key+'", "yourValue")<br/>'

        html_to_return += '.build();<br/>'
        html_to_return += '<br/>'

    html_to_return += 'Request request = new Request.Builder()<br/>'

    html_to_return += '.url("'+url+'")<br/>'

    if resource.request_type == 'GET':
        html_to_return += '.get()<br/>'
    else:
        html_to_return += '.post(requestBody)<br/>'

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