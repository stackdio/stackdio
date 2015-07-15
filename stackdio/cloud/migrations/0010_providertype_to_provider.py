# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0009_provider_to_account'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CloudProviderType',
            new_name='CloudProvider',
        ),
        migrations.RenameField(
            model_name='cloudprovider',
            old_name='type_name',
            new_name='name',
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
        migrations.AlterModelOptions(
            name='cloudaccount',
            options={'ordering': ('provider', 'title'), 'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
        migrations.AlterModelOptions(
            name='cloudregion',
            options={'ordering': ('provider', 'title'), 'default_permissions': ()},
        ),
        migrations.AlterUniqueTogether(
            name='cloudaccount',
            unique_together=set([('title', 'provider')]),
        ),
        migrations.AlterUniqueTogether(
            name='cloudregion',
            unique_together=set([('title', 'provider')]),
        ),
    ]
