# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-02 03:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0008_auto_20170302_1120'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parameter',
            name='role_name',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='\u89d2\u8272'),
        ),
    ]
