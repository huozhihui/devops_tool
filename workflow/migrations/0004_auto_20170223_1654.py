# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-02-23 08:54
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0003_auto_20170222_1503'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tasklog',
            old_name='host_id',
            new_name='host',
        ),
    ]
