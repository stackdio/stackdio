# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='stack',
            options={'ordering': ('title',), 'permissions': (('view_stack', 'Can view stack'), ('launch_stack', 'Can launch stack'), ('provision_stack', 'Can provision stack'), ('orchestrate_stack', 'Can orchestrate stack'), ('execute_stack', 'Can execute stack'), ('start_stack', 'Can start stack'), ('stop_stack', 'Can stop stack'), ('terminate_stack', 'Can terminate stack'))},
        ),
    ]
