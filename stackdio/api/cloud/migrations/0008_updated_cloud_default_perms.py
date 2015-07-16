# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0007_changed_model_permission_props'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cloudinstancesize',
            options={'ordering': ('id',), 'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='cloudprovidertype',
            options={'default_permissions': ('admin', 'view')},
        ),
        migrations.AlterModelOptions(
            name='cloudregion',
            options={'ordering': ('provider_type', 'title'), 'default_permissions': ()},
        ),
        migrations.AlterModelOptions(
            name='cloudzone',
            options={'ordering': ('region', 'title'), 'default_permissions': ()},
        ),
    ]
