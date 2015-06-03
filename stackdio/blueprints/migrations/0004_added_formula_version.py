# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0003_removed_owner_public'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlueprintFormulaVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('formula_url', models.URLField(verbose_name=b'Formula URL')),
                ('version', models.CharField(max_length=b'100', verbose_name=b'Version')),
                ('blueprint', models.ForeignKey(related_name='formula_versions', to='blueprints.Blueprint')),
            ],
        ),
    ]
