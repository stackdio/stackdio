# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_v0_7_migrations'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='advanced_view',
            field=models.BooleanField(default=False, verbose_name=b'Advanced View'),
        ),
    ]
