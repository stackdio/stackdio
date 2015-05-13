# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0002_added_circular_relation_fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cloudprofile',
            options={'default_permissions': ('create', 'view', 'update', 'delete')},
        ),
        migrations.AlterModelOptions(
            name='cloudprovider',
            options={'ordering': ('provider_type', 'title'), 'default_permissions': ('create', 'view', 'update', 'delete')},
        ),
        migrations.AlterModelOptions(
            name='snapshot',
            options={'default_permissions': ('create', 'view', 'update', 'delete')},
        ),
    ]
