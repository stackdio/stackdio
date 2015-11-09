# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import model_utils.fields
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Formula',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('status', model_utils.fields.StatusField(default=b'error', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'error', b'error'), (b'complete', b'complete'), (b'importing', b'importing')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('status_detail', models.TextField(blank=True)),
                ('public', models.BooleanField(default=False, verbose_name=b'Public')),
                ('uri', models.CharField(max_length=255, verbose_name=b'Repository URI')),
                ('root_path', models.CharField(max_length=64, verbose_name=b'Root Path')),
                ('git_username', models.CharField(max_length=64, verbose_name=b'Git Username (for private repos)', blank=True)),
                ('access_token', models.BooleanField(default=False, verbose_name=b'Access Token')),
                ('owner', models.ForeignKey(related_name='formulas', verbose_name=b'Owner', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='FormulaComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('sls_path', models.CharField(max_length=255)),
                ('formula', models.ForeignKey(related_name='components', to='formulas.Formula')),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
    ]
