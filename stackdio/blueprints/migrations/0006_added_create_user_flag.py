# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0005_changed_model_permission_props'),
    ]

    operations = [
        migrations.AddField(
            model_name='blueprint',
            name='create_users',
            field=models.BooleanField(default=True, verbose_name=b'Create SSH Users'),
            preserve_default=False,
        ),
    ]
