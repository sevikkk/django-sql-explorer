# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('explorer', '0011_auto_20150420_1542'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='groups',
            field=models.ManyToManyField(to='auth.Group', null=True),
        ),
    ]
