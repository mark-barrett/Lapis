# Developed by Mark Barrett
# https://markbarrettdesign.com
# https://github.com/mark-barrett
from django import template

from core.models import ResourceHeader, ResourceParameter, ResourceDataBind

register = template.Library()


@register.simple_tag()
def generate_resource_information(request, resource):

    html_to_return = ''

    # See if there are headers
    resource_headers = ResourceHeader.objects.all().filter(resource=resource)

    if resource_headers:
        html_to_return += '<p class="resource-heading">Headers</p>'

        html_to_return += '<table class="table table-striped table-sm">'
        html_to_return += '<thead><tr>'
        html_to_return += '<th scope="col">Key</th><th scope="col">Value</th><th scope="col">Description</th>'
        html_to_return += '</tr></thead>'
        html_to_return += '<tbody>'

        for header in resource_headers:
            html_to_return += '<tr><td>'+header.key+'</td><td>'+header.value+'</td><td>'+header.description+'</td></tr>'

        html_to_return += '</tbody>'

        html_to_return += '</table>'


    # Check if the request type is GET
    if resource.request_type == 'GET':
        # See if there are URL/GET Parameters
        resource_parameters = ResourceParameter.objects.all().filter(resource=resource)

        if resource_parameters:
            html_to_return += '<br/><p class="resource-heading">Parameters</p>'

            html_to_return += '<table class="table table-striped table-sm">'
            html_to_return += '<thead><tr>'
            html_to_return += '<th scope="col">Type</th><th scope="col">Key</th>'
            html_to_return += '</tr></thead>'
            html_to_return += '<tbody>'

            for parameter in resource_parameters:
                html_to_return += '<tr><td><span class="badge resource-parameter-label text-white resource-type-bg-'+parameter.type+'">' + parameter.type + '</span></td><td>' + parameter.key + '</td></tr>'

            html_to_return += '</tbody>'

            html_to_return += '</table>'

    elif resource.request_type == 'POST':
        # Get the data binds
        data_binds = ResourceDataBind.objects.all().filter(resource=resource)

        if data_binds:
            html_to_return += '<br/><p class="resource-heading">Attributes</p>'

            html_to_return += '<table class="table table-striped table-sm">'
            html_to_return += '<thead><tr>'
            html_to_return += '<th scope="col">Key</th><th scope="col">Type</th><th scope="col">Description</th>'
            html_to_return += '</tr></thead>'
            html_to_return += '<tbody>'

            for data_bind in data_binds:
                html_to_return += '<tr><td>'+data_bind.key+'</td><td>'+data_bind.type+'</td><td>'+data_bind.description+'</td></tr>'

            html_to_return += '</tbody>'

            html_to_return += '</table>'


    return html_to_return