# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import core.fields
import django.core.files.storage
import django.utils.timezone
from django.conf import settings
import django_extensions.db.fields
import blueprints.models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('formulas', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Blueprint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from=b'title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('public', models.BooleanField(default=False)),
                ('props_file', core.fields.DeletingFileField(default=None, upload_to=blueprints.models.get_props_file_path, storage=django.core.files.storage.FileSystemStorage(location=b'/Users/cperkins/.stackdio/storage'), max_length=255, blank=True, null=True)),
                ('owner', models.ForeignKey(related_name='blueprints', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BlueprintAccessRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from=b'title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('protocol', models.CharField(max_length=4, choices=[(b'tcp', b'TCP'), (b'udp', b'UDP'), (b'icmp', b'ICMP')])),
                ('from_port', models.IntegerField()),
                ('to_port', models.IntegerField()),
                ('rule', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name_plural': 'access rules',
            },
        ),
        migrations.CreateModel(
            name='BlueprintHostDefinition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from=b'title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('count', models.IntegerField()),
                ('hostname_template', models.CharField(max_length=64)),
                ('subnet_id', models.CharField(default=b'', max_length=32, blank=True)),
                ('spot_price', models.DecimalField(null=True, max_digits=5, decimal_places=2, blank=True)),
                ('blueprint', models.ForeignKey(related_name='host_definitions', to='blueprints.Blueprint')),
                ('cloud_profile', models.ForeignKey(related_name='host_definitions', to='cloud.CloudProfile')),
                ('size', models.ForeignKey(to='cloud.CloudInstanceSize')),
                ('zone', models.ForeignKey(blank=True, to='cloud.CloudZone', null=True)),
            ],
            options={
                'verbose_name_plural': 'host definitions',
            },
        ),
        migrations.CreateModel(
            name='BlueprintHostFormulaComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('order', models.IntegerField(default=0)),
                ('component', models.ForeignKey(to='formulas.FormulaComponent')),
                ('host', models.ForeignKey(related_name='formula_components', to='blueprints.BlueprintHostDefinition')),
            ],
            options={
                'ordering': ['order'],
                'verbose_name_plural': 'formula components',
            },
        ),
        migrations.CreateModel(
            name='BlueprintVolume',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', django_extensions.db.fields.AutoSlugField(populate_from=b'title', verbose_name='slug', editable=False, blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('device', models.CharField(max_length=32, choices=[(b'/dev/xvdj', b'/dev/xvdj'), (b'/dev/xvdk', b'/dev/xvdk'), (b'/dev/xvdl', b'/dev/xvdl'), (b'/dev/xvdm', b'/dev/xvdm'), (b'/dev/xvdn', b'/dev/xvdn')])),
                ('mount_point', models.CharField(max_length=64)),
                ('host', models.ForeignKey(related_name='volumes', to='blueprints.BlueprintHostDefinition')),
                ('snapshot', models.ForeignKey(related_name='host_definitions', to='cloud.Snapshot')),
            ],
            options={
                'verbose_name_plural': 'volumes',
            },
        ),
        migrations.AddField(
            model_name='blueprintaccessrule',
            name='host',
            field=models.ForeignKey(related_name='access_rules', to='blueprints.BlueprintHostDefinition'),
        ),
        migrations.AlterUniqueTogether(
            name='blueprint',
            unique_together=set([('owner', 'title')]),
        ),
    ]
