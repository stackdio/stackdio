# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blueprint',
            options={'default_permissions': ('create', 'view', 'update', 'delete')},
        ),
        migrations.AlterModelOptions(
            name='blueprintaccessrule',
            options={'default_permissions': (), 'verbose_name_plural': 'access rules'},
        ),
        migrations.AlterModelOptions(
            name='blueprinthostdefinition',
            options={'default_permissions': (), 'verbose_name_plural': 'host definitions'},
        ),
        migrations.AlterModelOptions(
            name='blueprinthostformulacomponent',
            options={'ordering': ['order'], 'default_permissions': (), 'verbose_name_plural': 'formula components'},
        ),
        migrations.AlterModelOptions(
            name='blueprintvolume',
            options={'default_permissions': (), 'verbose_name_plural': 'volumes'},
        ),
    ]
