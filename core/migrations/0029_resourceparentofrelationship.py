# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-02-16 18:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_auto_20190214_1802'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceParentOfRelationship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('child_table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='the_child_table', to='core.DatabaseTable')),
                ('child_table_column', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='the_column_in_the_child_table_to_match_to_the_parent_table', to='core.DatabaseColumn')),
                ('parent_table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='the_parent_table', to='core.DatabaseTable')),
                ('parent_table_column', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='the_column_in_the_parent_table_to_match_to_the_child_table', to='core.DatabaseColumn')),
            ],
            options={
                'verbose_name_plural': 'Resource Parent of Relationships',
            },
        ),
    ]
