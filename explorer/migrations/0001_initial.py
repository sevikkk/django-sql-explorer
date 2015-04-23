# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('sql', models.TextField()),
                ('description', models.TextField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_run_date', models.DateTimeField(auto_now=True)),
                ('cache_table', models.CharField(max_length=40, null=True, blank=True)),
                ('database', models.CharField(max_length=40, null=True, blank=True)),
                ('schedule', models.CharField(max_length=40, null=True, blank=True)),
                ('last_auto_run_date', models.DateTimeField(null=True, blank=True)),
                ('last_auto_run_result', models.TextField(max_length=10000, null=True, blank=True)),
                ('autorun_state', models.IntegerField(default=0)),
                ('post_cache_sql', models.TextField(max_length=10000, null=True, blank=True)),
                ('created_by_user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('groups', models.ManyToManyField(to='auth.Group')),
            ],
            options={
                'ordering': ['title'],
                'verbose_name_plural': 'Queries',
                'permissions': (('query_view', 'Can view queries'), ('query_view_any', 'Can view any queries')),
            },
        ),
        migrations.CreateModel(
            name='QueryLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sql', models.TextField()),
                ('database', models.TextField()),
                ('is_playground', models.BooleanField(default=False)),
                ('run_at', models.DateTimeField(auto_now_add=True)),
                ('query', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='explorer.Query', null=True)),
                ('run_by_user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-run_at'],
            },
        ),
    ]
