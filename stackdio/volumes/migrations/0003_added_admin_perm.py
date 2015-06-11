# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('volumes', '0002_added_permissions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='volume',
            options={'default_permissions': ('create', 'view', 'update', 'delete', 'admin')},
        ),
    ]
