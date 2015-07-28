# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0002_v0_7_migrations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stack',
            name='namespace',
            field=models.CharField(max_length=64, verbose_name=b'Namespace'),
        ),
        migrations.AlterUniqueTogether(
            name='stack',
            unique_together=set([('title',)]),
        ),
        migrations.RenameModel(
            old_name='StackAction',
            new_name='StackCommand',
        ),
        migrations.RemoveField(
            model_name='stackcommand',
            name='type',
        ),
    ]
