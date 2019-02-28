# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-02-27 17:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_resourcedatabind_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='request_type',
            field=models.CharField(choices=[('GET', 'GET'), ('POST', 'POST'), ('DELETE', 'DELETE')], max_length=4),
        ),
    ]