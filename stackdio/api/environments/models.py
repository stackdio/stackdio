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

import logging
import os

import salt.client
import six
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django_extensions.db.models import TimeStampedModel
from guardian.shortcuts import get_users_with_perms
from stackdio.core.constants import Activity, ComponentStatus, Health
from stackdio.core.fields import JSONField
from stackdio.core.utils import recursive_update

logger = logging.getLogger(__name__)


_environment_model_permissions = (
    'create',
    'admin',
)

_environment_object_permissions = (
    'view',
    'update',
    'ssh',
    'provision',
    'orchestrate',
    'delete',
    'admin',
)


class EnvironmentComponent(object):

    def __init__(self, environment, sls_path):
        super(EnvironmentComponent, self).__init__()
        self.environment = environment
        self.sls_path = sls_path
        self.metadatas = []

    def add_metadata(self, metadata):
        # Check to see if the host was already added
        for m in self.metadatas:
            if m.host == metadata.host:
                return
        self.metadatas.append(metadata)

    @property
    def health(self):
        return Health.aggregate([m.health for m in self.metadatas])

    @property
    def status(self):
        return ComponentStatus.aggregate([m.status for m in self.metadatas])


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

    activity = models.CharField('Activity',
                                max_length=32,
                                blank=True,
                                choices=Activity.ALL,
                                default=Activity.IDLE)

    create_users = models.BooleanField('Create SSH Users')

    labels = GenericRelation('core.Label')

    formula_versions = GenericRelation('formulas.FormulaVersion')

    # The properties for this blueprint
    properties = JSONField('Properties')

    orchestrate_sls_path = models.CharField('Orchestrate SLS Path', max_length=255,
                                            default='orchestrate')

    def __str__(self):
        return six.text_type('Environment {}'.format(self.name))

    @property
    def health(self):
        """
        Calculates the health of this stack from its hosts
        """
        healths = []

        for component in self.get_components():
            healths.append(component.health)

        return Health.aggregate(healths)

    def get_root_directory(self):
        return os.path.join(settings.FILE_STORAGE_DIRECTORY,
                            'environments',
                            six.text_type(self.name))

    def get_log_directory(self):
        root_dir = self.get_root_directory()
        log_dir = os.path.join(root_dir, 'logs')
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        return log_dir

    def get_full_pillar(self):
        users = []
        # pull the create_ssh_users property from the stackd.io config file.
        # If it's False, we won't create ssh users on the box.
        if self.create_users:
            user_permissions_map = get_users_with_perms(
                self, attach_perms=True, with_superusers=True, with_group_users=True
            )

            for user, perms in user_permissions_map.items():
                if 'ssh_environment' in perms:
                    if user.settings.public_key:
                        logger.debug('Granting {0} ssh permission to environment: {1}'.format(
                            user.username,
                            self.name,
                        ))
                        users.append({
                            'username': user.username,
                            'public_key': user.settings.public_key,
                            'id': user.id,
                        })
                    else:
                        logger.debug(
                            'User {0} has ssh permission for environment {1}, '
                            'but has no public key.  Skipping.'.format(
                                user.username,
                                self.name,
                            )
                        )

        pillar_props = {
            '__stackdio__': {
                'users': users
            }
        }

        # If any of the formulas we're using have default pillar
        # data defined in its corresponding SPECFILE, we need to pull
        # that into our environment pillar file.

        # for each unique formula, pull the properties from the SPECFILE
        for formula_version in self.formula_versions.all():
            formula = formula_version.formula
            version = formula_version.version

            # Update the formula
            formula.get_gitfs().update()

            # Add it to the rest of the pillar
            recursive_update(pillar_props, formula.properties(version))

        # Add in properties that were supplied via the blueprint and during
        # environment creation
        recursive_update(pillar_props, self.properties)

        return pillar_props

    def get_components(self):
        component_map = {}

        for metadata in self.component_metadatas.order_by('-modified'):
            if metadata.sls_path not in component_map:
                component_map[metadata.sls_path] = EnvironmentComponent(self, metadata.sls_path)

            component_map[metadata.sls_path].add_metadata(metadata)

        return sorted(component_map.values(), key=lambda x: x.sls_path)

    def get_current_component_metadata(self, sls_path, host):
        return self.component_metadatas.filter(
            sls_path=sls_path, host=host
        ).order_by('-modified').first()

    def set_component_status(self, sls_path, status, host_list):
        for host in host_list:
            current_metadata = self.get_current_component_metadata(sls_path, host)
            current_health = current_metadata.health if current_metadata else None
            self.component_metadatas.create(sls_path=sls_path,
                                            host=host,
                                            status=status,
                                            current_health=current_health)

    def get_current_hosts(self):
        client = salt.client.LocalClient(settings.STACKDIO_CONFIG.salt_master_config)

        result = client.cmd_iter('env:environments.{}'.format(self.name),
                                 'grains.items',
                                 expr_form='grain')

        ret = []
        for res in result:
            for data in res.values():
                if data.get('ret', False):
                    ret.append(data['ret'])

        return ret


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
