# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-02-20 17:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('docs', '0005_auto_20190220_1737'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentationinstance',
            name='project',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='core.Project'),
        ),
    ]