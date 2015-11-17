# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os

import git
from django.conf import settings
from django.db import migrations


def get_default_version(formula):
    repo_name = os.path.splitext(os.path.split(formula.uri)[-1])[0]

    repo_dir = os.path.join(
        settings.FILE_STORAGE_DIRECTORY,
        'formulas',
        '{0}-{1}'.format(formula.id, repo_name)
    )

    if not os.path.exists(repo_dir):
        return None

    repo = git.Repo(repo_dir)

    return str(repo.remotes.origin.refs.HEAD.ref.remote_head)


def forward(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    FormulaComponent = apps.get_model('formulas', 'FormulaComponent')
    FormulaVersion = apps.get_model('formulas', 'FormulaVersion')
    Stack = apps.get_model('stacks', 'Stack')
    Blueprint = apps.get_model('blueprints', 'Blueprint')
    HostDefinition = apps.get_model('blueprints', 'BlueprintHostDefinition')

    host_def_ctype = ContentType.objects.get(model='blueprinthostdefinition')

    def get_formulas(blueprint):
        formulas = set()
        for host_definition in HostDefinition.objects.filter(blueprint=blueprint):
            for component in FormulaComponent.objects.filter(object_id=host_definition.id,
                                                             content_type=host_def_ctype):
                formulas.add(component.formula)

        return list(formulas)

    if Stack.objects.count() > 0:
        stack_ctype = ContentType.objects.get(model='stack')

        for stack in Stack.objects.all():
            for formula in get_formulas(stack.blueprint):
                # Make sure the version doesn't already exist
                try:
                    FormulaVersion.objects.get(formula=formula, object_id=stack.id,
                                               content_type=stack_ctype)
                except FormulaVersion.DoesNotExist:
                    FormulaVersion.objects.create(formula=formula,
                                                  version=get_default_version(formula),
                                                  object_id=stack.id, content_type=stack_ctype)

    if Blueprint.objects.count() > 0:
        blueprint_ctype = ContentType.objects.get(model='blueprint')

        for blueprint in Blueprint.objects.all():
            for formula in get_formulas(blueprint):
                # Make sure the version doesn't already exist
                try:
                    FormulaVersion.objects.get(formula=formula, object_id=blueprint.id,
                                               content_type=blueprint_ctype)
                except FormulaVersion.DoesNotExist:
                    FormulaVersion.objects.create(formula=formula,
                                                  version=get_default_version(formula),
                                                  object_id=blueprint.id,
                                                  content_type=blueprint_ctype)


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0004_v0_7c_migrations'),
        ('stacks', '0005_v0_7d_migrations'),
        ('formulas', '0005_v0_7d_migrations'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
