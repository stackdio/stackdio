# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2016-12-07 16:43
from __future__ import unicode_literals

from django.db import migrations, models
import django_extensions.db.fields
import stackdio.core.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Environment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('properties', stackdio.core.fields.JSONField(verbose_name='Properties')),
            ],
            options={
                'ordering': ('name',),
                'default_permissions': ('admin', 'create', 'delete', 'update', 'view'),
            },
        ),
    ]
