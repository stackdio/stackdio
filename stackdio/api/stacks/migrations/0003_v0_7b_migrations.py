# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0002_v0_7_migrations'),
        ('cloud', '0005_v0_7b_migrations'),
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
        migrations.AlterField(
            model_name='stackcommand',
            name='stack',
            field=models.ForeignKey(related_name='commands', to='stacks.Stack'),
        ),
        migrations.AlterField(
            model_name='stackcommand',
            name='start',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name=b'Start Time', blank=True),
        ),
        migrations.RenameField(
            model_name='host',
            old_name='cloud_profile',
            new_name='cloud_image',
        ),
        migrations.AlterField(
            model_name='host',
            name='cloud_image',
            field=models.ForeignKey(related_name='hosts', to='cloud.CloudImage'),
        ),
    ]
