# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import json
import os

from django.db import migrations


def load_cloud_objects(apps, schema_editor):
    cloud_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    with open(os.path.join(cloud_dir, 'fixtures', 'initial_data.json')) as f:
        initial_data = json.load(f)

    if initial_data is None:
        print('Unable to load initial_data')

    for model in initial_data:
        model_cls = apps.get_model('cloud', model['model'])
        for object_data in model['objects']:
            model_cls.objects.create(**object_data)


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0004_removed_owner_public'),
    ]

    operations = [
        migrations.RunPython(load_cloud_objects),
    ]
