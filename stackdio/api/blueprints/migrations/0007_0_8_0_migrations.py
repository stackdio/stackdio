# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0006_0_8_0_migrations'),
    ]

    operations = [
        # Then delete the props_file field
        migrations.RemoveField(
            model_name='blueprint',
            name='props_file',
        ),
        migrations.RemoveField(
            model_name='blueprinthostdefinition',
            name='slug',
        ),
    ]
