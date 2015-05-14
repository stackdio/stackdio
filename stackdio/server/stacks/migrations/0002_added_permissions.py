# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='host',
            options={'ordering': ['blueprint_host_definition', '-index'], 'default_permissions': ('create', 'view', 'update', 'delete')},
        ),
        migrations.AlterModelOptions(
            name='stack',
            options={'ordering': ('title',), 'default_permissions': ('create', 'launch', 'view', 'update', 'provision', 'orchestrate', 'execute', 'start', 'stop', 'terminate', 'delete')},
        ),
        migrations.AlterModelOptions(
            name='stackaction',
            options={'default_permissions': (), 'verbose_name_plural': 'stack actions'},
        ),
        migrations.AlterModelOptions(
            name='stackhistory',
            options={'ordering': ['-created', '-id'], 'default_permissions': (), 'verbose_name_plural': 'stack history'},
        ),
        migrations.AlterField(
            model_name='stack',
            name='namespace',
            field=models.CharField(unique=True, max_length=64, verbose_name=b'Namespace', blank=True),
        ),
    ]
