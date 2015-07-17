# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('stacks', '0001_initial'),
        ('cloud', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Volume',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('hostname', models.CharField(max_length=64, verbose_name=b'Hostname')),
                ('volume_id', models.CharField(max_length=32, verbose_name=b'Volume ID', blank=True)),
                ('attach_time', models.DateTimeField(default=None, null=True, verbose_name=b'Attach Time', blank=True)),
                ('device', models.CharField(max_length=32, verbose_name=b'Device')),
                ('mount_point', models.CharField(max_length=255, verbose_name=b'Mount Point')),
                ('host', models.ForeignKey(related_name='volumes', on_delete=django.db.models.deletion.SET_NULL, to='stacks.Host', null=True)),
                ('snapshot', models.ForeignKey(to='cloud.Snapshot')),
                ('stack', models.ForeignKey(related_name='volumes', to='stacks.Stack')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
        ),
    ]
