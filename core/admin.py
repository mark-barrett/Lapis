from django.contrib import admin

from core.models import *

admin.site.register(Account)
admin.site.register(Project)
admin.site.register(Database)
admin.site.register(DatabaseTable)
admin.site.register(DatabaseColumn)
admin.site.register(Resource)
admin.site.register(ResourceHeader)
admin.site.register(ResourceParameter)
admin.site.register(ResourceDataSource)
admin.site.register(ResourceTextSource)
admin.site.register(ResourceDataSourceColumn)
admin.site.register(ResourceDataSourceFilter)
admin.site.register(ResourceParentChildRelationship)
admin.site.register(ResourceDataBind)
admin.site.register(UserGroup)
admin.site.register(ResourceUserGroup)
admin.site.register(BlockedIP)
admin.site.register(Alert)