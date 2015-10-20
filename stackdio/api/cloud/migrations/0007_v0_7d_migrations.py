# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0006_v0_7c_migrations'),
    ]

    operations = [
        migrations.AddField(
            model_name='cloudaccount',
            name='create_security_groups',
            field=models.BooleanField(default=True, verbose_name=b'Create Security Groups'),
        ),
    ]
