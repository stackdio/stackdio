# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0006_initial_data'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cloudprofile',
            options={'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
        migrations.AlterModelOptions(
            name='cloudprovider',
            options={'ordering': ('provider_type', 'title'), 'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
        migrations.AlterModelOptions(
            name='securitygroup',
            options={'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
        migrations.AlterModelOptions(
            name='snapshot',
            options={'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
    ]
