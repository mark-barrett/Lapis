# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-03-27 12:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_auto_20190327_1220'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resourceusergroup',
            name='resource',
        ),
        migrations.RemoveField(
            model_name='resourceusergroup',
            name='user_group',
        ),
        migrations.DeleteModel(
            name='ResourceUserGroup',
        ),
    ]
