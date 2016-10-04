# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('stacks', '0001_0_8_initial'),
        ('cloud', '0001_0_8_initial'),
    ]

    replaces = [
        ('cloud', '0001_initial'),
        ('cloud', '0002_initial'),
        ('cloud', '0004_v0_7_migrations'),
        ('cloud', '0005_v0_7b_migrations'),
        ('cloud', '0006_v0_7c_migrations'),
        ('cloud', '0007_v0_7d_migrations'),
        ('cloud', '0008_v0_7e_migrations'),
    ]

    operations = [
        migrations.AddField(
            model_name='securitygroup',
            name='stack',
            field=models.ForeignKey(related_name='security_groups', to='stacks.Stack', null=True),
        ),
        migrations.AddField(
            model_name='cloudzone',
            name='region',
            field=models.ForeignKey(related_name='zones', to='cloud.CloudRegion'),
        ),
        migrations.AddField(
            model_name='cloudregion',
            name='provider',
            field=models.ForeignKey(verbose_name='Cloud Provider', to='cloud.CloudProvider'),
        ),
        migrations.AddField(
            model_name='cloudinstancesize',
            name='provider',
            field=models.ForeignKey(verbose_name='Cloud Provider', to='cloud.CloudProvider'),
        ),
        migrations.AddField(
            model_name='cloudimage',
            name='account',
            field=models.ForeignKey(related_name='images', to='cloud.CloudAccount'),
        ),
        migrations.AddField(
            model_name='cloudimage',
            name='default_instance_size',
            field=models.ForeignKey(verbose_name='Default Instance Size', to='cloud.CloudInstanceSize'),
        ),
        migrations.AddField(
            model_name='cloudaccount',
            name='provider',
            field=models.ForeignKey(verbose_name='Cloud Provider', to='cloud.CloudProvider'),
        ),
        migrations.AddField(
            model_name='cloudaccount',
            name='region',
            field=models.ForeignKey(verbose_name='Region', to='cloud.CloudRegion'),
        ),
        migrations.AlterUniqueTogether(
            name='snapshot',
            unique_together=set([('snapshot_id', 'account')]),
        ),
        migrations.AlterUniqueTogether(
            name='securitygroup',
            unique_together=set([('name', 'account')]),
        ),
        migrations.AlterUniqueTogether(
            name='cloudzone',
            unique_together=set([('title', 'region')]),
        ),
        migrations.AlterUniqueTogether(
            name='cloudregion',
            unique_together=set([('title', 'provider')]),
        ),
        migrations.AlterUniqueTogether(
            name='cloudimage',
            unique_together=set([('title', 'account')]),
        ),
        migrations.AlterUniqueTogether(
            name='cloudaccount',
            unique_together=set([('title', 'provider')]),
        ),
    ]
