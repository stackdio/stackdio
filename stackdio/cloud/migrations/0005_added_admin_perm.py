# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0004_removed_owner_public'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cloudprofile',
            options={'default_permissions': ('create', 'view', 'update', 'delete', 'admin')},
        ),
        migrations.AlterModelOptions(
            name='cloudprovider',
            options={'ordering': ('provider_type', 'title'), 'default_permissions': ('create', 'view', 'update', 'delete', 'admin')},
        ),
        migrations.AlterModelOptions(
            name='securitygroup',
            options={'default_permissions': ('create', 'view', 'update', 'delete', 'admin')},
        ),
        migrations.AlterModelOptions(
            name='snapshot',
            options={'default_permissions': ('create', 'view', 'update', 'delete', 'admin')},
        ),
    ]
