# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    replaces = [
        ('core', '0001_initial'),
        ('core', '0002_v0_7_migrations'),
    ]

    operations = [
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=255, verbose_name='Key')),
                ('value', models.CharField(max_length=255, null=True, verbose_name='Value')),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='label',
            unique_together=set([('content_type', 'object_id', 'key')]),
        ),
    ]
