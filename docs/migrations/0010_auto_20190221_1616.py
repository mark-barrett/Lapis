# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-02-21 16:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docs', '0009_auto_20190221_1557'),
    ]

    operations = [
        migrations.AlterField(
            model_name='programminglanguagechoice',
            name='name',
            field=models.CharField(choices=[('curl', 'cURL'), ('python', 'Python'), ('java', 'Java'), ('javascript', 'JavaScript'), ('php', 'PHP')], max_length=32),
        ),
    ]