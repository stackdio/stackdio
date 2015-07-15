# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0005_added_admin_perm'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='stack',
            options={'ordering': ('title',), 'default_permissions': ('execute', 'delete', 'launch', 'admin', 'terminate', 'create', 'stop', 'update', 'start', 'orchestrate', 'provision', 'view')},
        ),
    ]
