# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-02-26 14:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0043_auto_20190226_1454'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcedatabind',
            name='description',
            field=models.CharField(default=1, max_length=256),
            preserve_default=False,
        ),
    ]
