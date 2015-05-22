# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0001_initial'),
        ('blueprints', '0001_initial'),
        ('cloud', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='securitygroup',
            name='blueprint_host_definition',
            field=models.ForeignKey(related_name='security_groups', default=None, to='blueprints.BlueprintHostDefinition', null=True),
        ),
        migrations.AddField(
            model_name='securitygroup',
            name='stack',
            field=models.ForeignKey(related_name='security_groups', to='stacks.Stack', null=True),
        ),
    ]
