# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-01 10:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0011_rolemanage_play_book'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rolemanage',
            old_name='play_book',
            new_name='playbook',
        ),
    ]