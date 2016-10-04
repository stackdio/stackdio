# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.core.files.storage
import django.utils.timezone
import django_extensions.db.fields
from django.conf import settings
from django.db import migrations, models

import stackdio.api.cloud.models
import stackdio.core.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('blueprints', '0001_0_8_initial'),
    ]

    replaces = [
        ('cloud', '0001_initial'),
        ('cloud', '0002_initial'),
        ('cloud', '0004_v0_7_migrations'),
        ('cloud', '0005_v0_7b_migrations'),
        ('cloud', '0006_v0_7c_migrations'),
        ('cloud', '0007_v0_7d_migrations'),
        ('cloud', '0008_v0_7e_migrations'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloudAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('yaml', models.TextField()),
                ('vpc_id', models.CharField(max_length=64, verbose_name='VPC ID', blank=True)),
                ('account_id', models.CharField(max_length=64, verbose_name='Account ID')),
                ('create_security_groups', models.BooleanField(default=True, verbose_name='Create Security Groups')),
                ('config_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.cloud.models.get_config_file_path, storage=django.core.files.storage.FileSystemStorage(location=settings.STACKDIO_CONFIG.salt_providers_dir), max_length=255, blank=True, null=True)),
                ('global_orch_props_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.cloud.models.get_global_orch_props_file_path, storage=django.core.files.storage.FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY), max_length=255, blank=True, null=True)),
            ],
            options={
                'ordering': ('title',),
                'default_permissions': ('admin', 'create', 'delete', 'update', 'view'),
            },
        ),
        migrations.CreateModel(
            name='CloudImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('image_id', models.CharField(max_length=64, verbose_name='Image ID')),
                ('ssh_user', models.CharField(max_length=64, verbose_name='SSH User')),
                ('config_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.cloud.models.get_config_file_path, storage=django.core.files.storage.FileSystemStorage(location=settings.STACKDIO_CONFIG.salt_profiles_dir), max_length=255, blank=True, null=True)),
            ],
            options={
                'ordering': ('title',),
                'default_permissions': ('admin', 'create', 'delete', 'update', 'view'),
            },
        ),
        migrations.CreateModel(
            name='CloudInstanceSize',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('instance_id', models.CharField(max_length=64, verbose_name='Instance ID')),
            ],
            options={
                'ordering': ('id',),
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='CloudProvider',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=32, verbose_name='Name', choices=[('ec2', 'Amazon Web Services')])),
            ],
            options={
                'default_permissions': ('admin', 'view'),
            },
        ),
        migrations.CreateModel(
            name='CloudRegion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
            ],
            options={
                'ordering': ('provider', 'title'),
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='CloudZone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
            ],
            options={
                'ordering': ('region', 'title'),
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='SecurityGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('group_id', models.CharField(max_length=16)),
                ('is_default', models.BooleanField(default=False)),
                ('is_managed', models.BooleanField(default=False)),
                ('account', models.ForeignKey(related_name='security_groups', to='cloud.CloudAccount')),
                ('blueprint_host_definition', models.ForeignKey(related_name='security_groups', default=None, to='blueprints.BlueprintHostDefinition', null=True)),
            ],
            options={
                'default_permissions': ('admin', 'create', 'delete', 'update', 'view'),
            },
        ),
        migrations.CreateModel(
            name='Snapshot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('snapshot_id', models.CharField(max_length=32)),
                ('size_in_gb', models.IntegerField()),
                ('filesystem_type', models.CharField(max_length=16, choices=[('ext2', 'ext2'), ('ext3', 'ext3'), ('ext4', 'ext4'), ('fuse', 'fuse'), ('xfs', 'xfs')])),
                ('account', models.ForeignKey(related_name='snapshots', to='cloud.CloudAccount')),
            ],
            options={
                'default_permissions': ('admin', 'create', 'delete', 'update', 'view'),
            },
        ),
    ]
