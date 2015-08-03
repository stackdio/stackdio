# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('formulas', '0002_v0_7_migrations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formula',
            name='git_username',
            field=models.CharField(max_length=64, verbose_name=b'Git Username', blank=True),
        ),
    ]
