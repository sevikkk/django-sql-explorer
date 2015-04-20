# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0003_auto_20150416_0907'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='last_auto_run_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='query',
            name='cache_table',
            field=models.CharField(max_length=40, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='query',
            name='database',
            field=models.CharField(max_length=40, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='query',
            name='schedule',
            field=models.CharField(max_length=40, null=True, blank=True),
        ),
    ]
