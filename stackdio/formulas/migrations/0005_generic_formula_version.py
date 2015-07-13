# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '__latest__'),
        ('formulas', '0004_updated_formula_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='FormulaVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('version', models.CharField(max_length=100, verbose_name=b'Formula Version')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('formula', models.ForeignKey(to='formulas.Formula')),
            ],
        ),
    ]
