# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-02-20 16:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docs', '0002_auto_20190220_1556'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentationinstance',
            name='enabled',
            field=models.BooleanField(default=False),
        ),
    ]