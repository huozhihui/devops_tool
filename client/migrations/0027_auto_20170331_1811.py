# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-31 18:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0026_auto_20170331_1623'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rolemanage',
            name='num',
            field=models.IntegerField(verbose_name='\u987a\u5e8f\u7f16\u53f7'),
        ),
    ]
