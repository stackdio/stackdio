# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import stackdio.api.stacks.models
import django.core.files.storage
import stackdio.core.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0004_v0_7c_migrations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stack',
            name='global_overstate_file',
        ),
        migrations.RemoveField(
            model_name='stack',
            name='overstate_file',
        ),
        migrations.AddField(
            model_name='stack',
            name='global_orchestrate_file',
            field=stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_orchestrate_file_path, storage=stackdio.api.stacks.models.stack_storage, max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='stack',
            name='orchestrate_file',
            field=stackdio.core.fields.DeletingFileField(default=None, upload_to=stackdio.api.stacks.models.get_orchestrate_file_path, storage=stackdio.api.stacks.models.stack_storage, max_length=255, blank=True, null=True),
        ),
    ]
