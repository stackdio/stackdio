# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0004_removed_permissions_from_host'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='stack',
            options={'ordering': ('title',), 'default_permissions': ('create', 'launch', 'view', 'update', 'provision', 'orchestrate', 'execute', 'start', 'stop', 'terminate', 'delete', 'admin')},
        ),
    ]
