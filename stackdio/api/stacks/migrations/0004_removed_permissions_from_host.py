# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0003_removed_owner_public'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='host',
            options={'ordering': ['blueprint_host_definition', '-index'], 'default_permissions': ()},
        ),
    ]
