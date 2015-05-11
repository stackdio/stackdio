# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('formulas', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='formula',
            options={'ordering': ['pk'], 'default_permissions': ('create', 'view', 'update', 'delete')},
        ),
    ]
