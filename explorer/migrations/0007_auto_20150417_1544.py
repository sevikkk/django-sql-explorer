# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('explorer', '0006_auto_20150417_1543'),
    ]

    operations = [
        migrations.RenameField(
            model_name='query',
            old_name='autorun_tate',
            new_name='autorun_state',
        ),
    ]
