# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import json
import os

from django.db import migrations


def load_initial_data():
    cloud_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    with open(os.path.join(cloud_dir, 'fixtures', 'initial_data.json')) as f:
        initial_data = json.load(f)

    if initial_data is None:
        print('Unable to load initial_data')

    return initial_data


def load_cloud_objects(apps, schema_editor):
    initial_data = load_initial_data()

    db_alias = schema_editor.connection.alias

    for model in initial_data:
        model_cls = apps.get_model('cloud', model['model'])
        to_create = []
        for object_data in model['objects']:
            to_create.append(model_cls(**object_data))

        model_cls.objects.using(db_alias).bulk_create(to_create)


def remove_cloud_objects(apps, schema_editor):
    initial_data = load_initial_data()

    for model in reversed(initial_data):
        model_cls = apps.get_model('cloud', model['model'])
        for model_object in model_cls.objects.all():
            model_object.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(load_cloud_objects, remove_cloud_objects),
    ]
