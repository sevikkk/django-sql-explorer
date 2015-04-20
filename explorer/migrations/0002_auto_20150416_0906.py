# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='cache_table',
            field=models.TextField(max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='query',
            name='database',
            field=models.TextField(max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='query',
            name='schedule',
            field=models.TextField(max_length=40, null=True),
        ),
    ]
