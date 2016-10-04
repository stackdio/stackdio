# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.utils.timezone
import django_extensions.db.fields
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    replaces = [
        ('formulas', '0001_initial'),
        ('formulas', '0002_v0_7_migrations'),
        ('formulas', '0003_v0_7b_migrations'),
        ('formulas', '0004_v0_7c_migrations'),
        ('formulas', '0005_v0_7d_migrations'),
        ('formulas', '0006_v0_7e_migrations'),
    ]

    operations = [
        migrations.CreateModel(
            name='Formula',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('status', model_utils.fields.StatusField(default=b'error', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'error', b'error'), (b'complete', b'complete'), (b'importing', b'importing')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('status_detail', models.TextField(blank=True)),
                ('uri', models.URLField(unique=True, verbose_name='Repository URI')),
                ('root_path', models.CharField(max_length=64, verbose_name='Root Path')),
                ('git_username', models.CharField(max_length=64, verbose_name='Git Username', blank=True)),
                ('access_token', models.BooleanField(default=False, verbose_name='Access Token')),
            ],
            options={
                'ordering': ['title'],
                'default_permissions': ('admin', 'create', 'delete', 'update', 'view'),
            },
        ),
        migrations.CreateModel(
            name='FormulaComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('sls_path', models.CharField(max_length=255)),
                ('object_id', models.PositiveIntegerField()),
                ('order', models.IntegerField(default=0, verbose_name='Order')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('formula', models.ForeignKey(to='formulas.Formula')),
            ],
            options={
                'ordering': ['order'],
                'default_permissions': (),
                'verbose_name_plural': 'formula components',
            },
        ),
        migrations.CreateModel(
            name='FormulaVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('version', models.CharField(max_length=100, verbose_name='Formula Version')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('formula', models.ForeignKey(to='formulas.Formula')),
            ],
            options={
                'default_permissions': (),
            },
        ),
    ]
