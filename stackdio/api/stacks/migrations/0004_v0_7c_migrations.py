# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('formulas', '0004_v0_7c_migrations'),
        ('stacks', '0003_v0_7b_migrations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='host',
            name='formula_components',
        ),
    ]
