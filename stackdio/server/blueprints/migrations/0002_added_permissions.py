# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blueprint',
            options={'permissions': (('view_blueprint', 'Can view blueprint'),)},
        ),
    ]
