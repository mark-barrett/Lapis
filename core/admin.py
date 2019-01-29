from django.contrib import admin

from core.models import *

admin.site.register(Account)
admin.site.register(Project)
admin.site.register(APIKey)
admin.site.register(Database)
admin.site.register(DatabaseTable)
admin.site.register(DatabaseColumn)
admin.site.register(Endpoint)
admin.site.register(EndpointHeader)
admin.site.register(EndpointParameter)
admin.site.register(EndpointDataSource)
admin.site.register(EndpointDataSourceColumn)
