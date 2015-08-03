# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import stackdio.api.cloud.models
import django.core.files.storage
import stackdio.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0004_v0_7_migrations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='securitygroup',
            name='group_id',
            field=models.CharField(max_length=16),
        ),
        migrations.RenameModel(
            old_name='CloudProfile',
            new_name='CloudImage',
        ),
        migrations.AlterField(
            model_name='cloudimage',
            name='account',
            field=models.ForeignKey(related_name='images', to='cloud.CloudAccount'),
        ),
    ]
