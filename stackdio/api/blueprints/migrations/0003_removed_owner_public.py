# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0002_added_permissions'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='blueprint',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='blueprint',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='blueprint',
            name='public',
        ),
    ]
