# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('formulas', '0002_added_permissions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='formula',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='formula',
            name='public',
        ),
    ]
