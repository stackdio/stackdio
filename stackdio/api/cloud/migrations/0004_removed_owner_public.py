# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0003_added_permissions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='securitygroup',
            name='owner',
        ),
    ]
