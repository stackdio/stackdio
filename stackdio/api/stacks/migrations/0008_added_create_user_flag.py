# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0007_added_ssh_perm'),
    ]

    operations = [
        migrations.AddField(
            model_name='stack',
            name='create_users',
            field=models.BooleanField(default=True, verbose_name=b'Create SSH Users'),
            preserve_default=False,
        ),
    ]
