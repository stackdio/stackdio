# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import django.core.files.base
from django.db import migrations


def get_properties(blueprint):
    if not blueprint.props_file:
        return {}
    with open(blueprint.props_file.path) as f:
        return json.loads(f.read())


def set_properties(blueprint, props):
    props_json = json.dumps(props, indent=4)
    if not blueprint.props_file:
        blueprint.props_file.save(blueprint.slug + '.props', django.core.files.base.ContentFile(props_json))
    else:
        with open(blueprint.props_file.path, 'w') as f:
            f.write(props_json)


def props_file_to_db(apps, schema_migration):
    Blueprint = apps.get_model('blueprints', 'Blueprint')

    for blueprint in Blueprint.objects.all():
        # Grab the properties from the file and save them to the database
        blueprint.properties = get_properties(blueprint)
        blueprint.save()


def db_to_props_file(apps, schema_migration):
    Blueprint = apps.get_model('blueprints', 'Blueprint')

    for blueprint in Blueprint.objects.all():
        # Grab the properties from the database and save them to the filesystem
        set_properties(blueprint, blueprint.properties)
        blueprint.save()


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0005_0_8_0_migrations'),
    ]

    operations = [
        # Then copy everything from all the props files into the properties field
        migrations.RunPython(props_file_to_db, db_to_props_file),
    ]
