# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import os

from django.conf import settings
from django.db import models, migrations
from six.moves.urllib_parse import urlsplit, urlunsplit

from stackdio.api.formulas.tasks import import_formula, FormulaTaskException
import shutil


def forward(apps, schema_editor):
    FormulaComponent = apps.get_model('formulas', 'FormulaComponent')
    Formula = apps.get_model('formulas', 'Formula')

    formulas = {}

    for formula in Formula.objects.all():
        # Get the username out of the URI if it's a private formula
        if formula.git_username:
            parse_res = urlsplit(formula.uri)
            if '@' in parse_res.netloc:
                new_netloc = parse_res.netloc.split('@')[-1]
                formula.uri = urlunsplit((
                    parse_res.scheme,
                    new_netloc,
                    parse_res.path,
                    parse_res.query,
                    parse_res.fragment
                ))
                formula.save()

        if formula.uri not in formulas:
            formulas[formula.uri] = formula
            continue

        # Otherwise we need to delete the formula and everything associated with it
        for component in FormulaComponent.objects.filter(formula=formula):
            for bhfc in component.blueprinthostformulacomponent_set.all():
                try:
                    bhfc.component = FormulaComponent.objects.get(sls_path=bhfc.component.sls_path,
                                                                  formula=formulas[formula.uri])
                    bhfc.save()
                except FormulaComponent.DoesNotExist:
                    bhfc.component.formula = formulas[formula.uri]
                    bhfc.component.save()

            component.delete()

        formula.delete()

    # re-import all the formulas
    for formula in Formula.objects.all():
        # there's nothing we can do about private repos without having the password :(
        if not formula.git_username:
            try:
                import_formula(formula.id, '')
            except FormulaTaskException as e:
                if 'SPECFILE' in e.message:
                    print('Skipping import of formula: {0}'.format(formula.uri))
                else:
                    raise
        else:
            print('Please manually update this formula via the API: {0}'.format(formula.uri))

    # remove the old ones
    old_formula_dir = os.path.join(settings.STACKDIO_CONFIG['storage_root'], 'user_states')
    if os.path.isdir(old_formula_dir):
        shutil.rmtree(old_formula_dir)


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('formulas', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forward),
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
