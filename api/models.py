from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from core.models import Resource, Project, UserGroup, Alert

# Projects can have API Keys
class APIKey(models.Model):
    # In form, the available column names are received when building the table but filtered by the selected table.
    key = models.CharField(max_length=64)
    user = models.ForeignKey(User)
    project = models.ForeignKey(Project)
    created_at = models.DateField(default=timezone.now)
    master = models.BooleanField(default=True)
    user_group = models.ForeignKey(UserGroup, blank=True, null=True)

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
        ('200 OK', '200 OK - Request was fine.'),
        ('400 ERR', '400 ERR - The request was incorrect.'),
        ('401 ERR', '401 ERR - No API key or the provided key is invalid.'),
        ('402 ERR', '402 ERR - The parameters were valid but the request failed.'),
        ('403 ERR', '403 ERR - The request is forbidden.'),
        ('404 ERR', '404 ERR - The requested resource does not exist.')
    )

    authentication_type = models.CharField(max_length=10, choices=AUTHENTICATION_TYPES)
    type = models.CharField(max_length=6, choices=REQUEST_TYPE)
    resource = models.CharField(max_length=64, blank=True, null=True)
    url = models.CharField(max_length=256)
    date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=8, choices=STATUS)
    ip_address = models.GenericIPAddressField()
    source = models.CharField(max_length=256)
    api_key = models.ForeignKey(APIKey, null=True, blank=True)
    response_to_user = models.TextField()
    # Field to basically store whehter or not this request has been accounted for by the cache
    cache = models.BooleanField(default=False)
    cached_result = models.BooleanField(default=False)

    def __str__(self):
       return self.status+' - '+str(self.date)+' - '+self.type

    class Meta:
        verbose_name_plural = 'API Requests'

    # this is not needed if small_image is created at set_image
    def save(self, *args, **kwargs):
        # Get all of the alerts, if they hit the limit then email.
        # Only if we have the API Key
        if self.api_key:
            try:
                # Get today
                today = datetime.today()

                alerts = Alert.objects.all().filter(resource=Resource.objects.get(name=self.resource, request_type=self.type, project=self.api_key.project))

                # Loop through alerts
                for alert in alerts:
                    api_requests = 0

                    # Check to see what the period is
                    if alert.period == 'day':
                        # If these arent equal, the notification has not been sent.
                        if alert.notification_sent_on.day != today.day:

                            api_requests = APIRequest.objects.all().filter(date__day=today.day).count()

                    elif alert.period == 'month':
                        # If these arent equal, the notification has not been sent.
                        if alert.notification_sent_on.month != today.month:

                            api_requests = APIRequest.objects.all().filter(date__month=today.month).count()

                    if alert.period == 'year':
                        # If these arent equal, the notification has not been sent.
                        if alert.notification_sent_on.year == today.year:

                            api_requests = APIRequest.objects.all().filter(date__year=today.year).count()

                    if alert.period == 'forever':

                        api_requests = APIRequest.objects.all().filter().count()

                    if api_requests >= alert.limit:
                        # Send the mail using celery.
                        from core.tasks import send_email
                        body = """
                            Hey, <br/><br/>

                            This is an automated email to let you know that the following resource has reached its request limit:<br/><br/>

                            <strong>Resource:</strong> {}<br/>
                            <strong>Limit:</strong> {}<br/>
                            <strong>Period:</strong> {}<br/>
                            <br/>
                            This is an automated email, please do not reply.<br/><br/>
                            Thank you and have a good day!<br/>
                            - Lapis
                        """.format(self.resource, str(alert.limit),
                                   str(alert.get_period_display()))

                        send_email.delay(alert.resource.project.alert_email, '[Lapis] ' + self.resource + ' Alert',
                                         body)

                        # Set the timezone of the notification to now so that the alert won't happen again in this period.
                        alert.notification_sent_on = timezone.now()

                        alert.save()
            except Exception as e:
                print(e)
                print('Cannot find alerts')

        super(APIRequest, self).save(*args, **kwargs)


