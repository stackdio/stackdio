# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0002_v0_7_migrations'),
        ('cloud', '0005_v0_7b_migrations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blueprintaccessrule',
            name='protocol',
            field=models.CharField(max_length=4, verbose_name=b'Protocol', choices=[(b'tcp', b'TCP'), (b'udp', b'UDP'), (b'icmp', b'ICMP'), (b'-1', b'all')]),
        ),
        migrations.AlterField(
            model_name='blueprinthostdefinition',
            name='count',
            field=models.PositiveIntegerField(verbose_name=b'Count'),
        ),
        migrations.AlterUniqueTogether(
            name='blueprinthostdefinition',
            unique_together=set([('title', 'blueprint'), ('hostname_template', 'blueprint')]),
        ),
        migrations.RenameField(
            model_name='blueprinthostdefinition',
            old_name='cloud_profile',
            new_name='cloud_image',
        ),
        migrations.AlterField(
            model_name='blueprinthostdefinition',
            name='cloud_image',
            field=models.ForeignKey(related_name='host_definitions', to='cloud.CloudImage'),
        ),
    ]
