# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import stackdio.core.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0004_0_8_0_migrations'),
    ]

    operations = [
        # Add the properties field first
        migrations.AddField(
            model_name='blueprint',
            name='properties',
            field=stackdio.core.fields.JSONField(verbose_name='Properties'),
        ),
    ]
