# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0013_auto_20150420_1844'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='query',
            options={'ordering': ['title'], 'verbose_name_plural': 'Queries', 'permissions': (('query_view', 'Can view queries'), ('query_view_any', 'Can view any queries'))},
        ),
    ]
