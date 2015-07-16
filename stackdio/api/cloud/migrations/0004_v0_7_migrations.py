# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from stackdio.api.cloud.utils import get_cloud_provider_choices

class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0003_initial_data'),
    ]

    operations = [
        # Rename the Provider -> Account
        migrations.RenameModel(
            old_name='CloudProvider',
            new_name='CloudAccount',
        ),
        migrations.RenameField(
            model_name='globalorchestrationformulacomponent',
            old_name='provider',
            new_name='account',
        ),
        migrations.AlterField(
            model_name='globalorchestrationformulacomponent',
            name='account',
            field=models.ForeignKey(to='cloud.CloudAccount', related_name='global_formula_components'),
        ),
        migrations.RenameField(
            model_name='cloudprofile',
            old_name='cloud_provider',
            new_name='account',
        ),
        migrations.AlterField(
            model_name='cloudprofile',
            name='account',
            field=models.ForeignKey(to='cloud.CloudAccount', related_name='profiles'),
        ),
        migrations.RenameField(
            model_name='securitygroup',
            old_name='cloud_provider',
            new_name='account',
        ),
        migrations.AlterField(
            model_name='securitygroup',
            name='account',
            field=models.ForeignKey(to='cloud.CloudAccount', related_name='security_groups'),
        ),
        migrations.RenameField(
            model_name='snapshot',
            old_name='cloud_provider',
            new_name='account',
        ),
        migrations.AlterField(
            model_name='snapshot',
            name='account',
            field=models.ForeignKey('cloud.CloudAccount', related_name='snapshots'),
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

        # Rename ProviderType -> Provider
        migrations.RenameModel(
            old_name='CloudProviderType',
            new_name='CloudProvider',
        ),
        migrations.RenameField(
            model_name='cloudprovider',
            old_name='type_name',
            new_name='name',
        ),
        migrations.AlterField(
            model_name='cloudprovider',
            name='name',
            field=models.CharField(unique=True, max_length=32, verbose_name=b'Name', choices=get_cloud_provider_choices()),
        ),
        migrations.RenameField(
            model_name='cloudinstancesize',
            old_name='provider_type',
            new_name='provider',
        ),
        migrations.AlterField(
            model_name='cloudinstancesize',
            name='provider',
            field=models.ForeignKey(verbose_name=b'Cloud Provider', to='cloud.CloudProvider'),
        ),
        migrations.RenameField(
            model_name='cloudaccount',
            old_name='provider_type',
            new_name='provider',
        ),
        migrations.AlterField(
            model_name='cloudaccount',
            name='provider',
            field=models.ForeignKey(verbose_name=b'Cloud Provider', to='cloud.CloudProvider'),
        ),
        migrations.RenameField(
            model_name='cloudregion',
            old_name='provider_type',
            new_name='provider',
        ),
        migrations.AlterField(
            model_name='cloudregion',
            name='provider',
            field=models.ForeignKey(verbose_name=b'Cloud Provider', to='cloud.CloudProvider'),
        ),
        migrations.AlterUniqueTogether(
            name='cloudaccount',
            unique_together=set([('title', 'provider')]),
        ),
        migrations.AlterUniqueTogether(
            name='cloudregion',
            unique_together=set([('title', 'provider')]),
        ),

        # Add default permissions
        migrations.AlterModelOptions(
            name='cloudinstancesize',
            options={'ordering': ('id',), 'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='cloudprofile',
            options={'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
        migrations.AlterModelOptions(
            name='cloudaccount',
            options={'ordering': ('provider', 'title'), 'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
        migrations.AlterModelOptions(
            name='cloudprovider',
            options={'default_permissions': ('admin', 'view',)},
        ),
        migrations.AlterModelOptions(
            name='cloudregion',
            options={'ordering': ('provider', 'title'), 'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='cloudzone',
            options={'ordering': ('region', 'title'), 'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='globalorchestrationformulacomponent',
            options={'ordering': ('order',), 'default_permissions': ('create', 'view', 'update', 'delete'), 'verbose_name_plural': 'global orchestration formula components'},
        ),
        migrations.AlterModelOptions(
            name='securitygroup',
            options={'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
        migrations.AlterModelOptions(
            name='snapshot',
            options={'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),

        # Remove appropriate fields
        migrations.RemoveField(
            model_name='securitygroup',
            name='owner',
        ),
    ]
