# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forward(apps, schema_editor):
    Blueprint = apps.get_model('blueprints', 'Blueprint')

    # We just want to add the owner in the description so we can figure out where it came from
    for blueprint in Blueprint.objects.all():
        blueprint.description = '{0} (previously owned by {1})'.format(blueprint.description,
                                                                       blueprint.owner.username)
        blueprint.save()


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forward),
        migrations.AlterModelOptions(
            name='blueprint',
            options={'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
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
        migrations.AlterUniqueTogether(
            name='blueprint',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='blueprint',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='blueprint',
            name='public',
        ),
        migrations.AddField(
            model_name='blueprint',
            name='create_users',
            field=models.BooleanField(default=True, verbose_name=b'Create SSH Users'),
            preserve_default=False,
        ),
    ]
