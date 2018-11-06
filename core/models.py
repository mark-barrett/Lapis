from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


# Extend the user model to add extra features to it
class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    endpoint_limit = models.IntegerField(default=10)

    class Meta:
        verbose_name_plural = 'Accounts'

    def __str__(self):
        return self.user.username


# Receivers to handle saving and updating the user model and its extended account model
@receiver(post_save, sender=User)
def create_user_account(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.account.save()
<<<<<<< HEAD


class Project(models.Model):
    name = models.CharField(max_length=64)
    description = models.TextField()
    user = models.ForeignKey(User)

    class Meta:
        unique_together = (('name', 'user'))
        verbose_name_plural = 'Projects'

    def __str__(self):
        return 'User: '+self.user.username+' Project:'+self.name
=======
>>>>>>> master
