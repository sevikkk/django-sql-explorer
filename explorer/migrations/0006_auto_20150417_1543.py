# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0005_query_autorun_in_progress'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='query',
            name='autorun_in_progress',
        ),
        migrations.AddField(
            model_name='query',
            name='autorun_tate',
            field=models.IntegerField(default=0),
        ),
    ]
