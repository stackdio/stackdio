# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '__latest__'),
        ('formulas', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='formula',
            options={'ordering': ['pk'], 'default_permissions': ('admin', 'create', 'delete', 'update', 'view')},
        ),
        migrations.AlterModelOptions(
            name='formulacomponent',
            options={'ordering': ['pk'], 'default_permissions': ()},
        ),
        migrations.RemoveField(
            model_name='formula',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='formula',
            name='public',
        ),
        migrations.AlterField(
            model_name='formula',
            name='uri',
            field=models.URLField(unique=True, verbose_name=b'Repository URI'),
        ),
        migrations.CreateModel(
            name='FormulaVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('version', models.CharField(max_length=100, verbose_name=b'Formula Version')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('formula', models.ForeignKey(to='formulas.Formula')),
            ],
            options={'default_permissions': ()},
        ),
    ]
