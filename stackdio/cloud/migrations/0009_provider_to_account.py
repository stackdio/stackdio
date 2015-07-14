# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import core.fields
import django.utils.timezone
import django.core.files.storage
import cloud.models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0008_updated_cloud_default_perms'),
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
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from=b'title', verbose_name='slug', editable=False, blank=True)),
                ('yaml', models.TextField()),
                ('vpc_id', models.CharField(max_length=64, verbose_name=b'VPC ID', blank=True)),
                ('account_id', models.CharField(max_length=64, verbose_name=b'Account ID')),
                ('config_file', core.fields.DeletingFileField(default=None, upload_to=cloud.models.get_config_file_path, storage=django.core.files.storage.FileSystemStorage(location=b'/home/stackdio/.stackdio/etc/salt/cloud.providers.d'), max_length=255, blank=True, null=True)),
                ('global_orch_props_file', core.fields.DeletingFileField(default=None, upload_to=cloud.models.get_global_orch_props_file_path, storage=django.core.files.storage.FileSystemStorage(location=b'/home/stackdio/.stackdio/storage'), max_length=255, blank=True, null=True)),
                ('provider_type', models.ForeignKey(verbose_name=b'Provider Type', to='cloud.CloudProviderType')),
                ('region', models.ForeignKey(verbose_name=b'Region', to='cloud.CloudRegion')),
            ],
            options={
                'ordering': ('provider_type', 'title'),
                'default_permissions': ('admin', 'create', 'delete', 'update', 'view'),
            },
        ),
        migrations.AlterUniqueTogether(
            name='cloudprovider',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='cloudprovider',
            name='provider_type',
        ),
        migrations.RemoveField(
            model_name='cloudprovider',
            name='region',
        ),
        migrations.RemoveField(
            model_name='globalorchestrationformulacomponent',
            name='provider',
        ),
        migrations.AlterUniqueTogether(
            name='cloudprofile',
            unique_together=set([('title', 'account')]),
        ),
        migrations.AlterUniqueTogether(
            name='securitygroup',
            unique_together=set([('name', 'account')]),
        ),
        migrations.AlterUniqueTogether(
            name='snapshot',
            unique_together=set([('snapshot_id', 'account')]),
        ),
        migrations.RemoveField(
            model_name='cloudprofile',
            name='cloud_provider',
        ),
        migrations.RemoveField(
            model_name='securitygroup',
            name='cloud_provider',
        ),
        migrations.RemoveField(
            model_name='snapshot',
            name='cloud_provider',
        ),
        migrations.AddField(
            model_name='cloudprofile',
            name='account',
            field=models.ForeignKey(related_name='profiles', default=1, to='cloud.CloudAccount'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='globalorchestrationformulacomponent',
            name='account',
            field=models.ForeignKey(related_name='global_formula_components', default=1, to='cloud.CloudAccount'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='securitygroup',
            name='account',
            field=models.ForeignKey(related_name='security_groups', default=1, to='cloud.CloudAccount'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='snapshot',
            name='account',
            field=models.ForeignKey(related_name='snapshots', default=1, to='cloud.CloudAccount'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='CloudProvider',
        ),
        migrations.AlterUniqueTogether(
            name='cloudaccount',
            unique_together=set([('title', 'provider_type')]),
        ),
    ]
