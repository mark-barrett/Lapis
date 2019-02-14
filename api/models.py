from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from core.models import Endpoint, Project


# Projects can have API Keys
class APIKey(models.Model):
    # In form, the available column names are received when building the table but filtered by the selected table.
    key = models.CharField(max_length=64)
    user = models.ForeignKey(User)
    project = models.ForeignKey(Project)
    created_at = models.DateField(default=timezone.now)
    master = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'API Keys'

    def __str__(self):
        return 'Key: '+self.key+ ' For: '+ self.project.name


class APIRequest(models.Model):
    AUTHENTICATION_TYPES = (
        ('KEY', 'Request was authorised by API key'),
        ('NO_AUTH', 'Request was not authorised.')
    )

    REQUEST_TYPE = (
        ('GET', 'GET Request'),
        ('POST', 'POST Request')
    )

    STATUS = (
        ('200 OK', '200 OK - Request was fine'),
        ('400 ERR', '400 ERR - The request was incorrect.'),
        ('401 ERR', '401 ERR - No API key or the provided key is invalid.')
    )

    authentication_type = models.CharField(max_length=10, choices=AUTHENTICATION_TYPES)
    type = models.CharField(max_length=6, choices=REQUEST_TYPE)
    resource = models.ForeignKey(Endpoint, blank=True, null=True)
    url = models.CharField(max_length=256)
    date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=8, choices=STATUS)
    ip_address = models.GenericIPAddressField()
    source = models.CharField(max_length=256)
    api_key = models.ForeignKey(APIKey, null=True, blank=True)

    def __str__(self):
       return self.status+' - '+str(self.date)+' - '+self.type

    class Meta:
        verbose_name_plural = 'API Requests'

