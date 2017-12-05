# -*- coding: utf-8 -*-

# Copyright 2017,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import unicode_literals

import io
import json
import logging
import os

from django.apps import AppConfig, apps
from django.core import exceptions
from django.db import DEFAULT_DB_ALIAS, router
from django.db.models.signals import post_migrate
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger(__name__)


def load_initial_data():
    cloud_dir = os.path.dirname(os.path.abspath(__file__))
    fixtures_json = os.path.join(cloud_dir, 'fixtures', 'cloud_objects.json')

    with io.open(fixtures_json, 'rt') as f:
        initial_data = json.load(f)

    if initial_data is None:
        logger.info('Unable to load cloud objects')

    return initial_data


def load_cloud_objects(app_config, verbosity=2, interactive=True,
                       using=DEFAULT_DB_ALIAS, **kwargs):

    if not app_config.models_module:
        return

    initial_data = load_initial_data()

    for model in initial_data:
        logger.info("Attempting to load data for {}...".format(model['model']))
        # Grab the model class, but don't fail if we can't find it
        try:
            model_cls = apps.get_model('cloud', model['model'])
        except LookupError:
            logger.warning('Failed to load model class: {}'.format(model['model']))
            continue

        # If we can't migrate this model, don't do anything & go on to the next
        if not router.allow_migrate_model(using, model_cls):
            logger.info("Skipping data load for {}".format(model['model']))
            continue

        to_create = []

        # Grab the attribute to filter on
        filter_attr = model['filter_attr']

        for object_data in model['objects']:
            # Only create if it's not already there
            filtered = model_cls.objects.filter(**{filter_attr: object_data[filter_attr]})

            if filtered.count() == 0:
                # Object doesn't exist in the database
                if 'pk' in object_data:
                    try:
                        model_cls.objects.get(pk=object_data['pk'])

                        # This means there's a conflicting pk, so we'll just remove the pk from
                        # the object_data dict and let it get assigned something else.
                        del object_data['pk']
                    except exceptions.ObjectDoesNotExist:
                        # There's no conflicting object, this is good
                        pass

                # Add this object to the create list
                to_create.append(model_cls(**object_data))
            else:
                # This object already exists in the database
                # Update the fields to match the new stuff if the object already exists
                for obj in filtered:
                    for attr, val in object_data.items():
                        # We don't want to change the object's primary key
                        #   it would mess up a bunch of relations
                        if attr != 'pk':
                            setattr(obj, attr, val)
                    obj.save()

        # bulk create everything
        model_cls.objects.using(using).bulk_create(to_create)


class CloudConfig(AppConfig):
    name = 'stackdio.api.cloud'
    verbose_name = _('Cloud')

    def ready(self):
        post_migrate.connect(load_cloud_objects, sender=self)
