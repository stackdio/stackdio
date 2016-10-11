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
import json
import os

import six
import yaml
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django_extensions.db.models import (
    TimeStampedModel,
    TitleSlugDescriptionModel,
)
from salt.version import __version__ as salt_version

from stackdio.core.queryset_transform import TransformQuerySet
from stackdio.core.fields import DeletingFileField
from stackdio.api.cloud.providers.base import GroupNotFoundException
from .utils import get_cloud_provider_choices, get_provider_driver_class

logger = logging.getLogger(__name__)

FILESYSTEM_CHOICES = (
    ('ext2', 'ext2'),
    ('ext3', 'ext3'),
    ('ext4', 'ext4'),
    ('fuse', 'fuse'),
    ('xfs', 'xfs'),
)


def get_config_file_path(instance, filename):
    return filename


def get_global_orch_props_file_path(instance, filename):
    return 'cloud/{0}/{1}'.format(instance.slug, filename)


_cloudprovider_model_permissions = ()
_cloudprovider_object_permissions = ('view', 'admin')


@six.python_2_unicode_compatible
class CloudProvider(models.Model):

    model_permissions = _cloudprovider_model_permissions
    object_permissions = _cloudprovider_object_permissions

    class Meta:
        default_permissions = tuple(set(_cloudprovider_model_permissions +
                                        _cloudprovider_object_permissions))

    PROVIDER_CHOICES = get_cloud_provider_choices()
    name = models.CharField(
        'Name',
        max_length=32,
        choices=PROVIDER_CHOICES,
        unique=True)

    def __str__(self):
        return six.text_type(self.name)

    def get_driver(self):
        # determine the provider driver class
        provider_class = get_provider_driver_class(self)

        # Return an instance of the provider driver
        return provider_class()


_cloudaccount_model_permissions = (
    'create',
    'admin',
)

_cloudaccount_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


@six.python_2_unicode_compatible
class CloudAccount(TimeStampedModel, TitleSlugDescriptionModel):

    model_permissions = _cloudaccount_model_permissions
    object_permissions = _cloudaccount_object_permissions
    searchable_fields = ('title', 'description')

    class Meta:
        ordering = ('title',)

        unique_together = ('title', 'provider')

        default_permissions = tuple(set(_cloudaccount_model_permissions +
                                        _cloudaccount_object_permissions))

    # What is the type of provider (e.g., AWS, Rackspace, etc)
    provider = models.ForeignKey('cloud.CloudProvider', verbose_name='Cloud Provider')

    # Used to store the provider-specifc YAML that will be written
    # to disk in settings.STACKDIO_CONFIG.salt_providers_dir
    yaml = models.TextField()

    # The region for this provider
    # FOR EC2 CLASSIC
    region = models.ForeignKey('CloudRegion', verbose_name='Region')

    # Are we using VPC?
    # FOR EC2 VPC
    vpc_id = models.CharField('VPC ID', max_length=64, blank=True)

    # If this is false, we won't create security groups on a per-stack basis.
    create_security_groups = models.BooleanField('Create Security Groups', default=True)

    # Grab the list of formula components
    formula_components = GenericRelation('formulas.FormulaComponent')

    # Grab the formula versions
    formula_versions = GenericRelation('formulas.FormulaVersion')

    # salt-cloud provider configuration file
    config_file = DeletingFileField(
        max_length=255,
        upload_to=get_config_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(
            location=settings.STACKDIO_CONFIG.salt_providers_dir))

    # storage for properties file
    global_orch_props_file = DeletingFileField(
        max_length=255,
        upload_to=get_global_orch_props_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    def __str__(self):
        return six.text_type(self.title)

    @property
    def vpc_enabled(self):
        return len(self.vpc_id) > 0

    def get_driver(self):
        # determine the provider driver class
        provider_class = get_provider_driver_class(self.provider)

        # Return an instance of the provider driver
        return provider_class(self)

    def update_config(self):
        """
        Writes the yaml configuration file for the given account object.
        """
        # update the account object's security group information
        security_groups = [sg.group_id for sg in self.security_groups.filter(
            is_default=True
        )]
        account_yaml = yaml.safe_load(self.yaml)
        account_yaml[self.slug]['securitygroupid'] = security_groups
        self.yaml = yaml.safe_dump(account_yaml, default_flow_style=False)
        self.save()

        if not self.config_file:
            self.config_file.save(self.slug + '.conf', ContentFile(self.yaml))
        else:
            with open(self.config_file.path, 'w') as f:
                # update the yaml to include updated security group information
                f.write(self.yaml)

    def _get_global_orchestration_properties(self):
        if not self.global_orch_props_file:
            return {}
        with open(self.global_orch_props_file.path) as f:
            return json.loads(f.read())

    def _set_global_orchestration_properties(self, props):
        props_json = json.dumps(props, indent=4)
        if not self.global_orch_props_file:
            self.global_orch_props_file.save('global_orch.props', ContentFile(props_json))
        else:
            with open(self.global_orch_props_file.path, 'w') as f:
                f.write(props_json)

    # Add as a property
    global_orchestration_properties = property(_get_global_orchestration_properties,
                                               _set_global_orchestration_properties)

    def get_root_directory(self):
        return os.path.join(settings.FILE_STORAGE_DIRECTORY, 'cloud', self.slug)

    def get_formulas(self):
        formulas = set()
        for component in self.formula_components.all():
            formulas.add(component.formula)

        return list(formulas)


@six.python_2_unicode_compatible
class CloudInstanceSize(TitleSlugDescriptionModel):
    class Meta:
        ordering = ('id',)

        default_permissions = ()

    # `title` field will be the type used by salt-cloud for the `size`
    # parameter in the providers yaml file (e.g., 'Micro Instance' or
    # '512MB Standard Instance'

    # link to the type of provider for this instance size
    provider = models.ForeignKey('cloud.CloudProvider',
                                 verbose_name='Cloud Provider',
                                 related_name='instance_sizes')

    # The underlying size ID of the instance (e.g., t1.micro)
    instance_id = models.CharField('Instance ID', max_length=64)

    def __str__(self):
        return six.text_type('{0} ({1})'.format(self.description, self.instance_id))


_cloudimage_model_permissions = (
    'create',
    'admin',
)

_cloudimage_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


@six.python_2_unicode_compatible
class CloudImage(TimeStampedModel, TitleSlugDescriptionModel):

    model_permissions = _cloudimage_model_permissions
    object_permissions = _cloudimage_object_permissions
    searchable_fields = ('title', 'description')

    class Meta:
        ordering = ('title',)

        unique_together = ('title', 'account')

        default_permissions = tuple(set(_cloudimage_model_permissions +
                                        _cloudimage_object_permissions))

    # What cloud account is this under?
    account = models.ForeignKey('cloud.CloudAccount', related_name='images')

    # The underlying image id of this image (e.g., ami-38df83a')
    image_id = models.CharField('Image ID', max_length=64)

    # The default instance size of this image, may be overridden
    # by the user at creation time
    default_instance_size = models.ForeignKey('CloudInstanceSize',
                                              verbose_name='Default Instance Size')

    # The SSH user that will have default access to the box. Salt-cloud
    # needs this to provision the box as a salt-minion and connect it
    # up to the salt-master automatically.
    ssh_user = models.CharField('SSH User', max_length=64)

    # salt-cloud profile configuration file
    config_file = DeletingFileField(
        max_length=255,
        upload_to=get_config_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(
            location=settings.STACKDIO_CONFIG.salt_profiles_dir
        )
    )

    def __str__(self):
        return six.text_type(self.title)

    def update_config(self):
        """
        Writes the salt-cloud profile configuration file
        """
        script = settings.STACKDIO_CONFIG.get('salt_bootstrap_script', 'bootstrap-salt')
        script_args = settings.STACKDIO_CONFIG.get('salt_bootstrap_args',
                                                   'stable archive/{salt_version}')

        profile_yaml = {
            self.slug: {
                'provider': self.account.slug,
                'image': self.image_id,
                'size': self.default_instance_size.title,
                'ssh_username': self.ssh_user,
                'script': script,
                'script_args': script_args.format(salt_version=salt_version),
                'sync_after_install': 'all',
                # PI-44: Need to add an empty minion config until salt-cloud/701
                # is fixed.
                'minion': {},
            }
        }
        profile_yaml = yaml.safe_dump(profile_yaml,
                                      default_flow_style=False)

        if not self.config_file:
            self.config_file.save(self.slug + '.conf', ContentFile(profile_yaml))
        else:
            with open(self.config_file.path, 'w') as f:
                # update the yaml to include updated security group information
                f.write(profile_yaml)

    def get_driver(self):
        return self.account.get_driver()


_snapshot_model_permissions = (
    'create',
    'admin',
)

_snapshot_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


@six.python_2_unicode_compatible
class Snapshot(TimeStampedModel, TitleSlugDescriptionModel):

    model_permissions = _snapshot_model_permissions
    object_permissions = _snapshot_object_permissions

    class Meta:
        unique_together = ('snapshot_id', 'account')

        default_permissions = tuple(set(_snapshot_model_permissions +
                                        _snapshot_object_permissions))

    # The cloud account that has access to this snapshot
    account = models.ForeignKey('cloud.CloudAccount', related_name='snapshots')

    # The snapshot id. Must exist already, be preformatted, and available
    # to the associated cloud account
    snapshot_id = models.CharField('Snapshot ID', max_length=32)

    # the type of file system the volume uses
    filesystem_type = models.CharField('Filesystem Type', max_length=16, choices=FILESYSTEM_CHOICES)

    def __str__(self):
        return six.text_type(self.snapshot_id)


@six.python_2_unicode_compatible
class CloudRegion(TitleSlugDescriptionModel):
    class Meta:
        unique_together = ('title', 'provider')
        ordering = ('provider', 'title')

        default_permissions = ()

    # link to the type of provider for this zone
    provider = models.ForeignKey('cloud.CloudProvider',
                                 verbose_name='Cloud Provider',
                                 related_name='regions')

    def __str__(self):
        return six.text_type(self.title)


@six.python_2_unicode_compatible
class CloudZone(TitleSlugDescriptionModel):
    class Meta:
        unique_together = ('title', 'region')
        ordering = ('region', 'title')

        default_permissions = ()

    # link to the region this AZ is in
    region = models.ForeignKey('cloud.CloudRegion',
                               verbose_name='Cloud Region',
                               related_name='zones')

    def __str__(self):
        return six.text_type(self.title)

    @property
    def provider(self):
        return self.region.provider


class SecurityGroupQuerySet(TransformQuerySet):
    def with_rules(self):
        return self.transform(self._inject_rules)

    def _inject_rules(self, queryset):
        """
        Pull all the security group rules using the cloud account's
        implementation.
        """
        by_account = {}
        for group in queryset:
            by_account.setdefault(group.account, []).append(group)

        for account, groups in by_account.items():
            group_ids = [group.group_id for group in groups]
            driver = account.get_driver()
            account_groups = driver.get_security_groups(group_ids)

            # add in the rules
            for group in groups:
                group.rules = account_groups[group.name]['rules']


_securitygroup_model_permissions = (
    'create',
    'admin',
)

_securitygroup_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


@six.python_2_unicode_compatible
class SecurityGroup(TimeStampedModel, models.Model):

    model_permissions = _securitygroup_model_permissions
    object_permissions = _securitygroup_object_permissions

    class Meta:
        unique_together = ('name', 'account')

        default_permissions = tuple(set(_securitygroup_model_permissions +
                                        _snapshot_object_permissions))

    objects = SecurityGroupQuerySet.as_manager()

    # Name of the security group (REQUIRED)
    name = models.CharField(max_length=255)

    # Description of the security group (REQUIRED)
    description = models.CharField(max_length=255)

    # ID given by the provider
    # NOTE: This will be set automatically after it has been created on the
    # account and will be ignored if passed in
    group_id = models.CharField(max_length=16)

    # The stack that the security group is for (this is only
    # useful if it's a managed security group)
    stack = models.ForeignKey(
        'stacks.Stack',
        null=True,
        related_name='security_groups'
    )

    blueprint_host_definition = models.ForeignKey(
        'blueprints.BlueprintHostDefinition',
        null=True,
        default=None,
        related_name='security_groups'
    )

    # the cloud account for this group
    account = models.ForeignKey('cloud.CloudAccount', related_name='security_groups')

    # ADMIN-ONLY: setting this to true will cause this security group
    # to be added automatically to all machines that get started in
    # the related cloud account
    is_default = models.BooleanField(default=False)

    # Flag for us to track which security groups were created by
    # stackd.io and should be managed by the system. Any stack
    # that is launched will have n security groups created and
    # managed, where n is the number of distinct host definitions
    # based on the blueprint used to create the stack
    is_managed = models.BooleanField(default=False)

    def __str__(self):
        return six.text_type(self.name)

    def get_active_hosts(self):
        return self.hosts.count()

    def rules(self):
        """
        Pulls the security groups using the cloud provider
        """
        driver = self.account.get_driver()
        groups = driver.get_security_groups([self.group_id])
        if len(groups) == 1:
            return groups[0].rules
        else:
            raise GroupNotFoundException('The group with id "{0}" was not '
                                         'found.'.format(self.group_id))
