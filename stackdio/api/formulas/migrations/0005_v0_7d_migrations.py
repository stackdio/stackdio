# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0004_v0_7c_migrations'),
        ('cloud', '0006_v0_7c_migrations'),
        ('formulas', '0004_v0_7c_migrations'),
    ]

    operations = [
        migrations.DeleteModel(
            name='FormulaComponent',
        ),
        migrations.RenameModel(
            old_name='FormulaComponent2',
            new_name='FormulaComponent',
        ),
    ]
