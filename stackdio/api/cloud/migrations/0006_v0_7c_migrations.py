# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('formulas', '0004_v0_7c_migrations'),
        ('cloud', '0005_v0_7b_migrations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='globalorchestrationformulacomponent',
            name='account',
        ),
        migrations.RemoveField(
            model_name='globalorchestrationformulacomponent',
            name='component',
        ),
        migrations.DeleteModel(
            name='GlobalOrchestrationFormulaComponent',
        ),
    ]
