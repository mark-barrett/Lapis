# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-02-14 11:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='apirequest',
            name='url',
            field=models.CharField(default=1, max_length=256),
            preserve_default=False,
        ),
    ]
