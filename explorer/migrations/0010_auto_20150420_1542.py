# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0009_query_post_cache_sql'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='query',
            options={'ordering': ['title'], 'verbose_name_plural': 'Queries', 'permissions': ('can_view', 'Can view query')},
        ),
    ]
