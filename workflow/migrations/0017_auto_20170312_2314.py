# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-12 23:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0016_task_result'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task_result',
            name='content',
            field=models.TextField(verbose_name='\u8fd4\u56de\u7ed3\u679c'),
        ),
    ]
