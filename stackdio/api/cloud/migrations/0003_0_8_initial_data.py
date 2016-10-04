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

    model_filter = {
        'CloudProvider': 'name',
        'CloudRegion': 'title',
        'CloudZone': 'title',
        'CloudInstanceSize': 'instance_id',
    }

    db_alias = schema_editor.connection.alias

    for model in initial_data:
        model_cls = apps.get_model('cloud', model['model'])
        to_create = []
        filter_attr = model_filter[model['model']]
        for object_data in model['objects']:
            # Only create if it's not already there
            filtered = model_cls.objects.filter(**{filter_attr: object_data[filter_attr]})
            if filtered.count() == 0:
                to_create.append(model_cls(**object_data))
            else:
                # Update the fields to match the new stuff if the object already exists
                for obj in filtered:
                    for attr, val in object_data.items():
                        setattr(obj, attr, val)
                    obj.save()

        model_cls.objects.using(db_alias).bulk_create(to_create)


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cloud', '0002_0_8_initial'),
    ]

    replaces = [
        ('cloud', '0003_initial_data'),
    ]

    operations = [
        migrations.RunPython(load_cloud_objects),
    ]
