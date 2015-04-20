# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0002_auto_20150416_0906'),
    ]

    operations = [
        migrations.AlterField(
            model_name='query',
            name='cache_table',
            field=models.CharField(max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='query',
            name='database',
            field=models.CharField(max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='query',
            name='schedule',
            field=models.CharField(max_length=40, null=True),
        ),
    ]
