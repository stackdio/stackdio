# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.core.files.storage
import django.utils.timezone
import django_extensions.db.fields
import model_utils.fields
from django.conf import settings
from django.db import migrations, models

import stackdio.api.stacks.models
import stackdio.core.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('blueprints', '0001_0_8_initial'),
        ('cloud', '0001_0_8_initial'),
    ]

    replaces = [
        ('stacks', '0001_initial'),
        ('stacks', '0002_v0_7_migrations'),
        ('stacks', '0003_v0_7b_migrations'),
        ('stacks', '0004_v0_7c_migrations'),
        ('stacks', '0005_v0_7d_migrations'),
    ]

    operations = [
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('status', model_utils.fields.StatusField(default='pending', max_length=100, verbose_name='status', no_check_for_status=True, choices=[('pending', 'pending'), ('ok', 'ok'), ('deleting', 'deleting')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('status_detail', models.TextField(blank=True)),
                ('subnet_id', models.CharField(default='', max_length=32, verbose_name='Subnet ID', blank=True)),
                ('hostname', models.CharField(max_length=64, verbose_name='Hostname')),
                ('index', models.IntegerField(verbose_name='Index')),
                ('state', models.CharField(default='unknown', max_length=32, verbose_name='State')),
                ('state_reason', models.CharField(default='', max_length=255, verbose_name='State Reason', blank=True)),
                ('provider_dns', models.CharField(max_length=64, verbose_name='Provider DNS', blank=True)),
                ('provider_private_dns', models.CharField(max_length=64, verbose_name='Provider Private DNS', blank=True)),
                ('provider_private_ip', models.CharField(max_length=64, verbose_name='Provider Private IP Address', blank=True)),
                ('fqdn', models.CharField(max_length=255, verbose_name='FQDN', blank=True)),
                ('instance_id', models.CharField(max_length=32, verbose_name='Instance ID', blank=True)),
                ('sir_id', models.CharField(default='unknown', max_length=32, verbose_name='SIR ID')),
                ('sir_price', models.DecimalField(null=True, verbose_name='Spot Price', max_digits=5, decimal_places=2)),
                ('availability_zone', models.ForeignKey(related_name='hosts', to='cloud.CloudZone', null=True)),
                ('blueprint_host_definition', models.ForeignKey(related_name='hosts', to='blueprints.BlueprintHostDefinition')),
                ('cloud_image', models.ForeignKey(related_name='hosts', to='cloud.CloudImage')),
                ('instance_size', models.ForeignKey(related_name='hosts', to='cloud.CloudInstanceSize')),
                ('security_groups', models.ManyToManyField(related_name='hosts', to='cloud.SecurityGroup')),
            ],
            options={
                'ordering': ['blueprint_host_definition', '-index'],
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='Stack',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('status', model_utils.fields.StatusField(default='pending', max_length=100, verbose_name='status', no_check_for_status=True, choices=[('pending', 'pending'), ('launching', 'launching'), ('configuring', 'configuring'), ('syncing', 'syncing'), ('provisioning', 'provisioning'), ('orchestrating', 'orchestrating'), ('finalizing', 'finalizing'), ('destroying', 'destroying'), ('finished', 'finished'), ('starting', 'starting'), ('stopping', 'stopping'), ('terminating', 'terminating'), ('executing_action', 'executing_action'), ('error', 'error')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('namespace', models.CharField(max_length=64, verbose_name='Namespace')),
                ('create_users', models.BooleanField(verbose_name='Create SSH Users')),
                ('map_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_local_file_path, storage=stackdio.api.stacks.models.stack_storage, max_length=255, blank=True, null=True)),
                ('top_file', stackdio.core.fields.DeletingFileField(default=None, upload_to='', storage=django.core.files.storage.FileSystemStorage(location=settings.STACKDIO_CONFIG.salt_core_states), max_length=255, blank=True, null=True)),
                ('orchestrate_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_orchestrate_file_path, storage=stackdio.api.stacks.models.stack_storage, max_length=255, blank=True, null=True)),
                ('global_orchestrate_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_orchestrate_file_path, storage=stackdio.api.stacks.models.stack_storage, max_length=255, blank=True, null=True)),
                ('pillar_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_local_file_path, storage=stackdio.api.stacks.models.stack_storage, max_length=255, blank=True, null=True)),
                ('global_pillar_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_local_file_path, storage=stackdio.api.stacks.models.stack_storage, max_length=255, blank=True, null=True)),
                ('props_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_local_file_path, storage=stackdio.api.stacks.models.stack_storage, max_length=255, blank=True, null=True)),
                ('blueprint', models.ForeignKey(related_name='stacks', to='blueprints.Blueprint')),
            ],
            options={
                'ordering': ('title',),
                'default_permissions': ('execute', 'delete', 'launch', 'admin', 'terminate', 'create', 'stop', 'update', 'start', 'ssh', 'orchestrate', 'provision', 'view'),
            },
        ),
        migrations.CreateModel(
            name='StackCommand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('status', model_utils.fields.StatusField(default='waiting', max_length=100, verbose_name='status', no_check_for_status=True, choices=[('waiting', 'waiting'), ('running', 'running'), ('finished', 'finished'), ('error', 'error')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('start', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Start Time', blank=True)),
                ('host_target', models.CharField(max_length=255, verbose_name='Host Target')),
                ('command', models.TextField(verbose_name='Command')),
                ('std_out_storage', models.TextField()),
                ('std_err_storage', models.TextField()),
                ('stack', models.ForeignKey(related_name='commands', to='stacks.Stack')),
            ],
            options={
                'default_permissions': (),
                'verbose_name_plural': 'stack actions',
            },
        ),
        migrations.CreateModel(
            name='StackHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('status', model_utils.fields.StatusField(default='pending', max_length=100, verbose_name='status', no_check_for_status=True, choices=[('pending', 'pending'), ('launching', 'launching'), ('configuring', 'configuring'), ('syncing', 'syncing'), ('provisioning', 'provisioning'), ('orchestrating', 'orchestrating'), ('finalizing', 'finalizing'), ('destroying', 'destroying'), ('finished', 'finished'), ('starting', 'starting'), ('stopping', 'stopping'), ('terminating', 'terminating'), ('executing_action', 'executing_action'), ('error', 'error')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('status_detail', models.TextField(blank=True)),
                ('event', models.CharField(max_length=128)),
                ('level', models.CharField(max_length=16, choices=[('DEBUG', 'DEBUG'), ('INFO', 'INFO'), ('WARNING', 'WARNING'), ('ERROR', 'ERROR')])),
                ('stack', models.ForeignKey(related_name='history', to='stacks.Stack')),
            ],
            options={
                'ordering': ['-created', '-id'],
                'default_permissions': (),
                'verbose_name_plural': 'stack history',
            },
        ),
        migrations.AddField(
            model_name='host',
            name='stack',
            field=models.ForeignKey(related_name='hosts', to='stacks.Stack'),
        ),
        migrations.AlterUniqueTogether(
            name='stack',
            unique_together=set([('title',)]),
        ),
    ]
