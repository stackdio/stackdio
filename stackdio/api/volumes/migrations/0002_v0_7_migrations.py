# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('volumes', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='volume',
            options={'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
    ]
