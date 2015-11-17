# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import stackdio.api.cloud.models
import django_extensions.db.fields
import stackdio.core.fields
from django.conf import settings
import django.utils.timezone
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('formulas', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloudInstanceSize',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('instance_id', models.CharField(max_length=64, verbose_name=b'Instance ID')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='CloudProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('image_id', models.CharField(max_length=64, verbose_name=b'Image ID')),
                ('ssh_user', models.CharField(max_length=64, verbose_name=b'SSH User')),
                ('config_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.cloud.models.get_config_file_path, storage=django.core.files.storage.FileSystemStorage(location=settings.STACKDIO_CONFIG.salt_profiles_dir), max_length=255, blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CloudProvider',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('yaml', models.TextField()),
                ('vpc_id', models.CharField(max_length=64, verbose_name=b'VPC ID', blank=True)),
                ('account_id', models.CharField(max_length=64, verbose_name=b'Account ID')),
                ('config_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.cloud.models.get_config_file_path, storage=django.core.files.storage.FileSystemStorage(location=settings.STACKDIO_CONFIG.salt_providers_dir), max_length=255, blank=True, null=True)),
                ('global_orch_props_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.cloud.models.get_global_orch_props_file_path, storage=django.core.files.storage.FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY), max_length=255, blank=True, null=True)),
            ],
            options={
                'ordering': ('provider_type', 'title'),
            },
        ),
        migrations.CreateModel(
            name='CloudProviderType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type_name', models.CharField(unique=True, max_length=32, verbose_name=b'Type Name', choices=[(b'ec2', b'Amazon Web Services')])),
            ],
        ),
        migrations.CreateModel(
            name='CloudRegion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('provider_type', models.ForeignKey(to='cloud.CloudProviderType')),
            ],
            options={
                'ordering': ('provider_type', 'title'),
            },
        ),
        migrations.CreateModel(
            name='CloudZone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('region', models.ForeignKey(related_name='zones', to='cloud.CloudRegion')),
            ],
            options={
                'ordering': ('region', 'title'),
            },
        ),
        migrations.CreateModel(
            name='GlobalOrchestrationFormulaComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('order', models.IntegerField(default=0)),
                ('component', models.ForeignKey(to='formulas.FormulaComponent')),
                ('provider', models.ForeignKey(related_name='global_formula_components', to='cloud.CloudProvider')),
            ],
            options={
                'ordering': ('order',),
                'verbose_name_plural': 'global orchestration formula components',
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
                ('group_id', models.CharField(max_length=16, blank=True)),
                ('is_default', models.BooleanField(default=False)),
                ('is_managed', models.BooleanField(default=False)),
                ('cloud_provider', models.ForeignKey(related_name='security_groups', to='cloud.CloudProvider')),
                ('owner', models.ForeignKey(related_name='security_groups', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Snapshot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('snapshot_id', models.CharField(max_length=32)),
                ('size_in_gb', models.IntegerField()),
                ('filesystem_type', models.CharField(max_length=16, choices=[(b'ext2', b'ext2'), (b'ext3', b'ext3'), (b'ext4', b'ext4'), (b'fuse', b'fuse'), (b'xfs', b'xfs')])),
                ('cloud_provider', models.ForeignKey(related_name='snapshots', to='cloud.CloudProvider')),
            ],
        ),
        migrations.AddField(
            model_name='cloudprovider',
            name='provider_type',
            field=models.ForeignKey(verbose_name=b'Provider Type', to='cloud.CloudProviderType'),
        ),
        migrations.AddField(
            model_name='cloudprovider',
            name='region',
            field=models.ForeignKey(verbose_name=b'Region', to='cloud.CloudRegion'),
        ),
        migrations.AddField(
            model_name='cloudprofile',
            name='cloud_provider',
            field=models.ForeignKey(related_name='profiles', to='cloud.CloudProvider'),
        ),
        migrations.AddField(
            model_name='cloudprofile',
            name='default_instance_size',
            field=models.ForeignKey(verbose_name=b'Default Instance Size', to='cloud.CloudInstanceSize'),
        ),
        migrations.AddField(
            model_name='cloudinstancesize',
            name='provider_type',
            field=models.ForeignKey(verbose_name=b'Provider Type', to='cloud.CloudProviderType'),
        ),
        migrations.AlterUniqueTogether(
            name='snapshot',
            unique_together=set([('snapshot_id', 'cloud_provider')]),
        ),
        migrations.AlterUniqueTogether(
            name='securitygroup',
            unique_together=set([('name', 'cloud_provider')]),
        ),
        migrations.AlterUniqueTogether(
            name='cloudzone',
            unique_together=set([('title', 'region')]),
        ),
        migrations.AlterUniqueTogether(
            name='cloudregion',
            unique_together=set([('title', 'provider_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='cloudprovider',
            unique_together=set([('title', 'provider_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='cloudprofile',
            unique_together=set([('title', 'cloud_provider')]),
        ),
    ]
