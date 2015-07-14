# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0008_updated_cloud_default_perms'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CloudProvider',
            new_name='CloudAccount',
        ),
        migrations.RenameField(
            model_name='globalorchestrationformulacomponent',
            old_name='provider',
            new_name='account',
        ),
        migrations.RenameField(
            model_name='cloudprofile',
            old_name='cloud_provider',
            new_name='account',
        ),
        migrations.RenameField(
            model_name='securitygroup',
            old_name='cloud_provider',
            new_name='account',
        ),
        migrations.RenameField(
            model_name='snapshot',
            old_name='cloud_provider',
            new_name='account',
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
    ]
