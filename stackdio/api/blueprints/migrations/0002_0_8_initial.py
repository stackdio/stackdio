# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('blueprints', '0001_0_8_initial'),
        ('cloud', '0001_0_8_initial'),
    ]

    replaces = [
        ('blueprints', '0001_initial'),
        ('blueprints', '0002_v0_7_migrations'),
        ('blueprints', '0003_v0_7b_migrations'),
        ('blueprints', '0004_v0_7c_migrations'),
        ('blueprints', '0005_v0_7d_migrations'),
    ]

    operations = [
        migrations.AddField(
            model_name='blueprintvolume',
            name='snapshot',
            field=models.ForeignKey(related_name='host_definitions', to='cloud.Snapshot'),
        ),
        migrations.AddField(
            model_name='blueprinthostdefinition',
            name='blueprint',
            field=models.ForeignKey(related_name='host_definitions', to='blueprints.Blueprint'),
        ),
        migrations.AddField(
            model_name='blueprinthostdefinition',
            name='cloud_image',
            field=models.ForeignKey(related_name='host_definitions', to='cloud.CloudImage'),
        ),
        migrations.AddField(
            model_name='blueprinthostdefinition',
            name='size',
            field=models.ForeignKey(to='cloud.CloudInstanceSize'),
        ),
        migrations.AddField(
            model_name='blueprinthostdefinition',
            name='zone',
            field=models.ForeignKey(blank=True, to='cloud.CloudZone', null=True),
        ),
        migrations.AddField(
            model_name='blueprintaccessrule',
            name='host',
            field=models.ForeignKey(related_name='access_rules', to='blueprints.BlueprintHostDefinition'),
        ),
        migrations.AlterUniqueTogether(
            name='blueprinthostdefinition',
            unique_together=set([('title', 'blueprint'), ('hostname_template', 'blueprint')]),
        ),
    ]
