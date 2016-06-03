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
        (b'blueprints', '0001_initial'),
        (b'blueprints', '0002_v0_7_migrations'),
        (b'blueprints', '0003_v0_7b_migrations'),
        (b'blueprints', '0004_v0_7c_migrations'),
        (b'blueprints', '0005_v0_7d_migrations'),
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
                ('create_users', models.BooleanField(verbose_name=b'Create SSH Users')),
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
                ('protocol', models.CharField(max_length=4, verbose_name=b'Protocol', choices=[(b'tcp', b'TCP'), (b'udp', b'UDP'), (b'icmp', b'ICMP'), (b'-1', b'all')])),
                ('from_port', models.IntegerField(verbose_name=b'Start Port')),
                ('to_port', models.IntegerField(verbose_name=b'End Port')),
                ('rule', models.CharField(max_length=255, verbose_name=b'Rule')),
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
                ('count', models.PositiveIntegerField(verbose_name=b'Count')),
                ('hostname_template', models.CharField(max_length=64, verbose_name=b'Hostname Template')),
                ('subnet_id', models.CharField(default=b'', max_length=32, verbose_name=b'Subnet ID', blank=True)),
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
                ('device', models.CharField(max_length=32, verbose_name=b'Device Name', choices=[(b'/dev/sdb', b'/dev/sdb'), (b'/dev/sdc', b'/dev/sdc'), (b'/dev/sdd', b'/dev/sdd'), (b'/dev/sde', b'/dev/sde'), (b'/dev/sdf', b'/dev/sdf'), (b'/dev/sdg', b'/dev/sdg'), (b'/dev/sdh', b'/dev/sdh'), (b'/dev/sdi', b'/dev/sdi'), (b'/dev/sdj', b'/dev/sdj'), (b'/dev/sdk', b'/dev/sdk'), (b'/dev/sdl', b'/dev/sdl')])),
                ('mount_point', models.CharField(max_length=64, verbose_name=b'Mount Point')),
                ('host', models.ForeignKey(related_name='volumes', to='blueprints.BlueprintHostDefinition')),
            ],
            options={
                'default_permissions': (),
                'verbose_name_plural': 'volumes',
            },
        ),
    ]
