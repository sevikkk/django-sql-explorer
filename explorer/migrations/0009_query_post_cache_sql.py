# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0008_query_last_auto_run_result'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='post_cache_sql',
            field=models.TextField(max_length=10000, null=True, blank=True),
        ),
    ]
