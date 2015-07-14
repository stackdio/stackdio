# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('formulas', '0006_added_admin_perm'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='formula',
            options={'ordering': ['pk'], 'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
        migrations.AlterModelOptions(
            name='formulaversion',
            options={'default_permissions': ()},
        ),
    ]
