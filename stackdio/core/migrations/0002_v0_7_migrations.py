# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='label',
            name='value',
            field=models.CharField(max_length=255, null=True, verbose_name=b'Value'),
        ),
    ]
