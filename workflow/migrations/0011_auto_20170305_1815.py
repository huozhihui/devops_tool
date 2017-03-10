# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-05 10:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0010_task_role_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasklog',
            name='begin_deploy_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tasklog',
            name='timeout',
            field=models.IntegerField(default=180),
        ),
    ]
