# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('formulas', '0003_removed_owner_public'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formula',
            name='uri',
            field=models.URLField(unique=True, verbose_name=b'Repository URI'),
        ),
    ]
