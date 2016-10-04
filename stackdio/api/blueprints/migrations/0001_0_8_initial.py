# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.core.files.storage
import django.utils.timezone
import django_extensions.db.fields
from django.conf import settings
from django.db import migrations, models

import stackdio.api.blueprints.models
import stackdio.core.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    replaces = [
        ('blueprints', '0001_initial'),
        ('blueprints', '0002_v0_7_migrations'),
        ('blueprints', '0003_v0_7b_migrations'),
        ('blueprints', '0004_v0_7c_migrations'),
        ('blueprints', '0005_v0_7d_migrations'),
    ]

    operations = [
        migrations.CreateModel(
            name='Blueprint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('create_users', models.BooleanField(verbose_name='Create SSH Users')),
                ('props_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.blueprints.models.get_props_file_path, storage=django.core.files.storage.FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY), max_length=255, blank=True, null=True)),
            ],
            options={
                'ordering': ('title',),
                'default_permissions': ('admin', 'create', 'delete', 'update', 'view'),
            },
        ),
        migrations.CreateModel(
            name='BlueprintAccessRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('protocol', models.CharField(max_length=4, verbose_name='Protocol', choices=[('tcp', 'TCP'), ('udp', 'UDP'), ('icmp', 'ICMP'), ('-1', 'all')])),
                ('from_port', models.IntegerField(verbose_name='Start Port')),
                ('to_port', models.IntegerField(verbose_name='End Port')),
                ('rule', models.CharField(max_length=255, verbose_name='Rule')),
            ],
            options={
                'default_permissions': (),
                'verbose_name_plural': 'access rules',
            },
        ),
        migrations.CreateModel(
            name='BlueprintHostDefinition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('count', models.PositiveIntegerField(verbose_name='Count')),
                ('hostname_template', models.CharField(max_length=64, verbose_name='Hostname Template')),
                ('subnet_id', models.CharField(default='', max_length=32, verbose_name='Subnet ID', blank=True)),
                ('spot_price', models.DecimalField(null=True, max_digits=5, decimal_places=2, blank=True)),
            ],
            options={
                'verbose_name_plural': 'host definitions',
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='BlueprintVolume',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('device', models.CharField(max_length=32, verbose_name='Device Name', choices=[('/dev/sdb', '/dev/sdb'), ('/dev/sdc', '/dev/sdc'), ('/dev/sdd', '/dev/sdd'), ('/dev/sde', '/dev/sde'), ('/dev/sdf', '/dev/sdf'), ('/dev/sdg', '/dev/sdg'), ('/dev/sdh', '/dev/sdh'), ('/dev/sdi', '/dev/sdi'), ('/dev/sdj', '/dev/sdj'), ('/dev/sdk', '/dev/sdk'), ('/dev/sdl', '/dev/sdl')])),
                ('mount_point', models.CharField(max_length=64, verbose_name='Mount Point')),
                ('host', models.ForeignKey(related_name='volumes', to='blueprints.BlueprintHostDefinition')),
            ],
            options={
                'default_permissions': (),
                'verbose_name_plural': 'volumes',
            },
        ),
    ]
