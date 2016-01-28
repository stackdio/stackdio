# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0007_v0_7d_migrations'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cloudaccount',
            options={'ordering': ('title',), 'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
        migrations.AlterModelOptions(
            name='cloudimage',
            options={'ordering': ('title',), 'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
    ]
