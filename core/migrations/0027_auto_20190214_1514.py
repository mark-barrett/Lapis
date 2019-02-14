# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-02-14 15:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_auto_20190214_1204'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resource',
            name='resource_url',
        ),
        migrations.AlterField(
            model_name='resource',
            name='name',
            field=models.CharField(max_length=64, unique=True),
        ),
    ]
