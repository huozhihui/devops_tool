# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-01 09:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0006_auto_20170228_1851'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasklog',
            name='role_name',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
