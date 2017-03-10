# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-10 10:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hostgroup',
            name='describe',
            field=models.CharField(default=1, max_length=255, verbose_name='\u63cf\u8ff0'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='host',
            name='conn_status',
            field=models.BooleanField(default=False, verbose_name='\u8fde\u63a5\u72b6\u6001'),
        ),
        migrations.AlterField(
            model_name='host',
            name='describe',
            field=models.CharField(max_length=255, verbose_name='\u63cf\u8ff0'),
        ),
        migrations.AlterField(
            model_name='host',
            name='host_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.HostGroup', verbose_name='\u96b6\u5c5e\u7ec4'),
        ),
        migrations.AlterField(
            model_name='host',
            name='ip',
            field=models.GenericIPAddressField(verbose_name='IP'),
        ),
        migrations.AlterField(
            model_name='host',
            name='password',
            field=models.CharField(max_length=30, verbose_name='password'),
        ),
        migrations.AlterField(
            model_name='host',
            name='port',
            field=models.IntegerField(default=22, verbose_name='\u7aef\u53e3'),
        ),
        migrations.AlterField(
            model_name='host',
            name='username',
            field=models.CharField(max_length=30, verbose_name='\u7528\u6237\u540d'),
        ),
    ]