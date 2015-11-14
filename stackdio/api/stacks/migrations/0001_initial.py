# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import model_utils.fields
import django_extensions.db.fields
import stackdio.core.fields
import django.core.files.storage
import django.utils.timezone
from django.conf import settings
import stackdio.api.stacks.models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blueprints', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('status', model_utils.fields.StatusField(default=b'pending', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'pending', b'pending'), (b'ok', b'ok'), (b'deleting', b'deleting')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('status_detail', models.TextField(blank=True)),
                ('subnet_id', models.CharField(default=b'', max_length=32, verbose_name=b'Subnet ID', blank=True)),
                ('hostname', models.CharField(max_length=64, verbose_name=b'Hostname')),
                ('index', models.IntegerField(verbose_name=b'Index')),
                ('state', models.CharField(default=b'unknown', max_length=32, verbose_name=b'State')),
                ('state_reason', models.CharField(default=b'', max_length=255, verbose_name=b'State Reason', blank=True)),
                ('provider_dns', models.CharField(max_length=64, verbose_name=b'Provider DNS', blank=True)),
                ('provider_private_dns', models.CharField(max_length=64, verbose_name=b'Provider Private DNS', blank=True)),
                ('provider_private_ip', models.CharField(max_length=64, verbose_name=b'Provider Private IP Address', blank=True)),
                ('fqdn', models.CharField(max_length=255, verbose_name=b'FQDN', blank=True)),
                ('instance_id', models.CharField(max_length=32, verbose_name=b'Instance ID', blank=True)),
                ('sir_id', models.CharField(default=b'unknown', max_length=32, verbose_name=b'SIR ID')),
                ('sir_price', models.DecimalField(null=True, verbose_name=b'Spot Price', max_digits=5, decimal_places=2)),
                ('availability_zone', models.ForeignKey(related_name='hosts', to='cloud.CloudZone', null=True)),
                ('blueprint_host_definition', models.ForeignKey(related_name='hosts', to='blueprints.BlueprintHostDefinition')),
                ('cloud_profile', models.ForeignKey(related_name='hosts', to='cloud.CloudProfile')),
                ('formula_components', models.ManyToManyField(related_name='hosts', to='blueprints.BlueprintHostFormulaComponent')),
                ('instance_size', models.ForeignKey(related_name='hosts', to='cloud.CloudInstanceSize')),
                ('security_groups', models.ManyToManyField(related_name='hosts', to='cloud.SecurityGroup')),
            ],
            options={
                'ordering': ['blueprint_host_definition', '-index'],
            },
        ),
        migrations.CreateModel(
            name='Stack',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from='title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('status', model_utils.fields.StatusField(default=b'pending', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'pending', b'pending'), (b'launching', b'launching'), (b'configuring', b'configuring'), (b'syncing', b'syncing'), (b'provisioning', b'provisioning'), (b'orchestrating', b'orchestrating'), (b'finalizing', b'finalizing'), (b'destroying', b'destroying'), (b'finished', b'finished'), (b'starting', b'starting'), (b'stopping', b'stopping'), (b'terminating', b'terminating'), (b'executing_action', b'executing_action'), (b'error', b'error')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('namespace', models.CharField(max_length=64, verbose_name=b'Namespace', blank=True)),
                ('public', models.BooleanField(default=False, verbose_name=b'Public')),
                ('map_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_local_file_path, storage=stackdio.api.stacks.models.stack_storage, max_length=255, blank=True, null=True)),
                ('top_file', stackdio.core.fields.DeletingFileField(default=None, storage=django.core.files.storage.FileSystemStorage(location=settings.STACKDIO_CONFIG.salt_core_states), max_length=255, blank=True, null=True)),
                ('overstate_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_orchestrate_file_path, storage=django.core.files.storage.FileSystemStorage(location=settings.STACKDIO_CONFIG.salt_core_states), max_length=255, blank=True, null=True)),
                ('global_overstate_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_orchestrate_file_path, storage=django.core.files.storage.FileSystemStorage(location=settings.STACKDIO_CONFIG.salt_core_states), max_length=255, blank=True, null=True)),
                ('pillar_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_local_file_path, storage=stackdio.api.stacks.models.stack_storage, max_length=255, blank=True, null=True)),
                ('global_pillar_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_local_file_path, storage=stackdio.api.stacks.models.stack_storage, max_length=255, blank=True, null=True)),
                ('props_file', stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_local_file_path, storage=stackdio.api.stacks.models.stack_storage, max_length=255, blank=True, null=True)),
                ('blueprint', models.ForeignKey(related_name='stacks', to='blueprints.Blueprint')),
                ('owner', models.ForeignKey(related_name='stacks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('title',),
            },
        ),
        migrations.CreateModel(
            name='StackAction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('status', model_utils.fields.StatusField(default=b'waiting', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'waiting', b'waiting'), (b'running', b'running'), (b'finished', b'finished'), (b'error', b'error')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('start', models.DateTimeField(verbose_name=b'Start Time')),
                ('type', models.CharField(max_length=50, verbose_name=b'Action Type')),
                ('host_target', models.CharField(max_length=255, verbose_name=b'Host Target')),
                ('command', models.TextField(verbose_name=b'Command')),
                ('std_out_storage', models.TextField()),
                ('std_err_storage', models.TextField()),
                ('stack', models.ForeignKey(related_name='actions', to='stacks.Stack')),
            ],
            options={
                'verbose_name_plural': 'stack actions',
            },
        ),
        migrations.CreateModel(
            name='StackHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('status', model_utils.fields.StatusField(default=b'pending', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'pending', b'pending'), (b'launching', b'launching'), (b'configuring', b'configuring'), (b'syncing', b'syncing'), (b'provisioning', b'provisioning'), (b'orchestrating', b'orchestrating'), (b'finalizing', b'finalizing'), (b'destroying', b'destroying'), (b'finished', b'finished'), (b'starting', b'starting'), (b'stopping', b'stopping'), (b'terminating', b'terminating'), (b'executing_action', b'executing_action'), (b'error', b'error')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('status_detail', models.TextField(blank=True)),
                ('event', models.CharField(max_length=128)),
                ('level', models.CharField(max_length=16, choices=[(b'DEBUG', b'DEBUG'), (b'INFO', b'INFO'), (b'WARNING', b'WARNING'), (b'ERROR', b'ERROR')])),
                ('stack', models.ForeignKey(related_name='history', to='stacks.Stack')),
            ],
            options={
                'ordering': ['-created', '-id'],
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
            unique_together=set([('owner', 'title')]),
        ),
    ]
