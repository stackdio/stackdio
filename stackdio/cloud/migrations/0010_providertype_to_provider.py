# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0009_provider_to_account'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloudProvider',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=32, verbose_name=b'Name', choices=[(b'ec2', b'Amazon Web Services')])),
            ],
            options={
                'default_permissions': ('admin', 'view'),
            },
        ),
        migrations.AlterModelOptions(
            name='cloudaccount',
            options={'ordering': ('provider', 'title'), 'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
        migrations.AlterModelOptions(
            name='cloudregion',
            options={'ordering': ('provider', 'title'), 'default_permissions': ()},
        ),
        migrations.RemoveField(
            model_name='cloudinstancesize',
            name='provider_type',
        ),
        migrations.AlterUniqueTogether(
            name='cloudaccount',
            unique_together=set([('title', 'provider')]),
        ),
        migrations.AlterUniqueTogether(
            name='cloudregion',
            unique_together=set([('title', 'provider')]),
        ),
        migrations.RemoveField(
            model_name='cloudaccount',
            name='provider_type',
        ),
        migrations.RemoveField(
            model_name='cloudregion',
            name='provider_type',
        ),
        migrations.AddField(
            model_name='cloudaccount',
            name='provider',
            field=models.ForeignKey(default=1, verbose_name=b'Cloud Provider', to='cloud.CloudProvider'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cloudinstancesize',
            name='provider',
            field=models.ForeignKey(default=1, verbose_name=b'Cloud Provider', to='cloud.CloudProvider'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cloudregion',
            name='provider',
            field=models.ForeignKey(default=1, verbose_name=b'Cloud Provider', to='cloud.CloudProvider'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='CloudProviderType',
        ),
    ]
