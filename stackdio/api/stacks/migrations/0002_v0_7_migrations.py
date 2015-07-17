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
            options={'ordering': ['blueprint_host_definition', '-index'], 'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='stack',
            options={'ordering': ('title',), 'default_permissions': ('execute', 'delete', 'launch', 'admin', 'terminate', 'create', 'stop', 'update', 'start', 'ssh', 'orchestrate', 'provision', 'view')},
        ),
        migrations.AlterModelOptions(
            name='stackaction',
            options={'default_permissions': (), 'verbose_name_plural': 'stack actions'},
        ),
        migrations.AlterModelOptions(
            name='stackhistory',
            options={'ordering': ['-created', '-id'], 'default_permissions': (), 'verbose_name_plural': 'stack history'},
        ),
        migrations.AlterUniqueTogether(
            name='stack',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='stack',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='stack',
            name='public',
        ),
        migrations.AddField(
            model_name='stack',
            name='create_users',
            field=models.BooleanField(default=True, verbose_name=b'Create SSH Users'),
            preserve_default=False,
        ),
    ]
