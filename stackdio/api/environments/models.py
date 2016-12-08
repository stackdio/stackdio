# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
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

import logging

import six
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django_extensions.db.models import TimeStampedModel
from stackdio.core.constants import ComponentStatus, Health
from stackdio.core.fields import JSONField

logger = logging.getLogger(__name__)


_environment_model_permissions = (
    'create',
    'admin',
)

_environment_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


@six.python_2_unicode_compatible
class Environment(TimeStampedModel):

    model_permissions = _environment_model_permissions
    object_permissions = _environment_object_permissions

    class Meta:
        ordering = ('name',)
        default_permissions = tuple(set(_environment_model_permissions +
                                        _environment_object_permissions))

    name = models.CharField('Name', max_length=255, unique=True)
    description = models.TextField('Description', blank=True, null=True)

    labels = GenericRelation('core.Label')

    formula_versions = GenericRelation('formulas.FormulaVersion')

    # The properties for this blueprint
    properties = JSONField('Properties')

    def __str__(self):
        return six.text_type('Environment {}'.format(self.name))


class ComponentMetadataQuerySet(models.QuerySet):

    def create(self, **kwargs):
        if 'health' not in kwargs:
            current_health = kwargs.pop('current_health', None)
            if 'status' in kwargs:
                kwargs['health'] = ComponentMetadata.HEALTH_MAP[kwargs['status']] \
                                   or current_health \
                                   or Health.UNKNOWN
        return super(ComponentMetadataQuerySet, self).create(**kwargs)


@six.python_2_unicode_compatible
class ComponentMetadata(TimeStampedModel):

    # Limited health map - since we don't know what the components are,
    # we can't know if they're queued / running.
    HEALTH_MAP = {
        ComponentStatus.SUCCEEDED: Health.HEALTHY,
        ComponentStatus.FAILED: Health.UNHEALTHY,
        ComponentStatus.CANCELLED: None,
    }

    STATUS_CHOICES = tuple((x, x) for x in set(HEALTH_MAP.keys()))
    HEALTH_CHOICES = tuple((x, x) for x in set(HEALTH_MAP.values()) if x is not None)

    # Fields
    sls_path = models.CharField('SLS Path', max_length=128)

    host = models.CharField('Host', max_length=256)

    environment = models.ForeignKey('Environment', related_name='component_metadatas')

    status = models.CharField('Status',
                              max_length=32,
                              choices=STATUS_CHOICES,
                              default=ComponentStatus.QUEUED)

    health = models.CharField('Health',
                              max_length=32,
                              choices=HEALTH_CHOICES,
                              default=Health.UNKNOWN)

    objects = ComponentMetadataQuerySet.as_manager()

    def __str__(self):
        return six.text_type('Component {} for environment {} - {} ({})'.format(
            self.sls_path,
            self.environment.name,
            self.status,
            self.health,
        ))

    def set_status(self, status):
        # Make sure it's a valid status
        assert status in self.HEALTH_MAP

        self.status = status

        # Set the health based on the new status
        new_health = self.HEALTH_MAP[status]

        if new_health is not None:
            self.health = new_health

        self.save()
