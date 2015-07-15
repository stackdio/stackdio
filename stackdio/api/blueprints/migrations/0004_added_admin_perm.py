# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0003_removed_owner_public'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blueprint',
            options={'default_permissions': ('create', 'view', 'update', 'delete', 'admin')},
        ),
    ]
