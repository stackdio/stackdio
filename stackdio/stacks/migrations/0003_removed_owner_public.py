# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0002_added_permissions'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='stack',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='stack',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='stack',
            name='public',
        ),
    ]
