# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0006_changed_model_permission_props'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='stack',
            options={'ordering': ('title',), 'default_permissions': ('execute', 'delete', 'launch', 'admin', 'terminate', 'create', 'stop', 'update', 'start', 'ssh', 'orchestrate', 'provision', 'view')},
        ),
    ]
