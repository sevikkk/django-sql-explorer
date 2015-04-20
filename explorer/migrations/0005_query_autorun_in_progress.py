# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0004_auto_20150417_1438'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='autorun_in_progress',
            field=models.BooleanField(default=False),
        ),
    ]
