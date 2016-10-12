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

# pylint: disable=too-many-lines

from __future__ import unicode_literals

import collections
import json
import logging
import os
import re

import salt.cloud
import six
import yaml
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db import models, transaction
from django.dispatch import receiver
from django.utils.lru_cache import lru_cache
from django.utils.timezone import now
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel
from guardian.shortcuts import get_users_with_perms
from model_utils import Choices
from model_utils.models import StatusModel
from rest_framework.exceptions import APIException
from stackdio.api.cloud.models import SecurityGroup
from stackdio.api.cloud.providers.base import GroupExistsException
from stackdio.api.volumes.models import Volume
from stackdio.core.constants import Health, ComponentStatus, Activity
from stackdio.core.decorators import django_cache
from stackdio.core.fields import DeletingFileField, JSONField
from stackdio.core.models import SearchQuerySet
from stackdio.core.notifications.decorators import add_subscribed_channels
from stackdio.core.utils import recursive_update

logger = logging.getLogger(__name__)

# Set any options that are not allowed to be in a host's EXTRA_OPTIONS
INSTANCE_OPTION_BLACKLIST = ['name', 'minion', 'size', 'securitygroupid', 'volumes',
                             'driver', 'id', 'key', 'keyname', 'private_key', 'append_domain',
                             'location', 'ssh_interface', 'image', 'provider', 'ssh_username']

PROTOCOL_CHOICES = [
    ('tcp', 'TCP'),
    ('udp', 'UDP'),
    ('icmp', 'ICMP'),
]

HOST_INDEX_PATTERN = re.compile(r'.*-.*-(\d+)')

DEFAULT_FILESYSTEM_TYPE = settings.STACKDIO_CONFIG.get('default_fs_type', 'ext4')


def get_hostnames_from_hostdefs(hostdefs, username='', namespace=''):
    hostnames = []
    for hostdef in hostdefs:
        for i in range(hostdef.count):
            hostnames.append(
                hostdef.hostname_template.format(
                    namespace=namespace,
                    username=username,
                    index=i
                )
            )
    return hostnames


class StackCreationException(Exception):
    def __init__(self, errors, *args, **kwargs):
        self.errors = errors
        super(StackCreationException, self).__init__(*args, **kwargs)


class StackQuerySet(SearchQuerySet):
    searchable_fields = ('title', 'description', 'history__message')

    def create(self, **kwargs):
        new_properties = kwargs.pop('properties', {})

        with transaction.atomic(using=self.db):
            stack = super(StackQuerySet, self).create(**kwargs)

            # manage the properties
            properties = stack.blueprint.properties
            recursive_update(properties, new_properties)

            stack.properties = properties

            # Create the appropriate hosts & security group objects
            stack.create_security_groups()
            stack.create_hosts()

        return stack


_stack_model_permissions = (
    'create',
    'admin',
)

_stack_object_permissions = (
    'launch',
    'view',
    'update',
    'ssh',
    'provision',
    'orchestrate',
    'execute',
    'pause',
    'resume',
    'terminate',
    'delete',
    'admin',
)

stack_storage = FileSystemStorage(location=os.path.join(settings.FILE_STORAGE_DIRECTORY, 'stacks'))


# For map, pillar, and properties.  Doesn't need to go in a sub directory
def get_local_file_path(instance, filename):
    return '{0}-{1}/{2}'.format(instance.pk, instance.slug, filename)


# Orchestrate files go in formula directory
def get_orchestrate_file_path(instance, filename):
    return '{0}-{1}/formulas/__stackdio__/{2}'.format(instance.pk, instance.slug, filename)


@add_subscribed_channels
@six.python_2_unicode_compatible
class Stack(TimeStampedModel, TitleSlugDescriptionModel):
    """
    The basic model for a stack
    """
    model_permissions = _stack_model_permissions
    object_permissions = _stack_object_permissions

    class Meta:
        ordering = ('title',)

        default_permissions = tuple(set(_stack_model_permissions + _stack_object_permissions))

        unique_together = ('title',)

    activity = models.CharField('Activity',
                                max_length=32,
                                blank=True,
                                choices=Activity.ALL,
                                default=Activity.QUEUED)

    # What blueprint did this stack derive from?
    blueprint = models.ForeignKey('blueprints.Blueprint', related_name='stacks')

    formula_versions = GenericRelation('formulas.FormulaVersion')

    labels = GenericRelation('core.Label')

    # An arbitrary namespace for this stack. Mainly useful for Blueprint
    # hostname templates
    namespace = models.CharField('Namespace', max_length=64)

    create_users = models.BooleanField('Create SSH Users')

    # Where on disk is the salt-cloud map file stored
    map_file = DeletingFileField(
        max_length=255,
        upload_to=get_local_file_path,
        null=True,
        blank=True,
        default=None,
        storage=stack_storage)

    # Where on disk is the custom salt top.sls file stored
    top_file = DeletingFileField(
        max_length=255,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.STACKDIO_CONFIG.salt_core_states))

    # Where on disk is the custom orchestrate file stored
    orchestrate_file = DeletingFileField(
        max_length=255,
        upload_to=get_orchestrate_file_path,
        null=True,
        blank=True,
        default=None,
        storage=stack_storage)

    # Where on disk is the global orchestrate file stored
    global_orchestrate_file = DeletingFileField(
        max_length=255,
        upload_to=get_orchestrate_file_path,
        null=True,
        blank=True,
        default=None,
        storage=stack_storage)

    # Where on disk is the custom pillar file for custom configuration for
    # all salt states used by the top file
    pillar_file = DeletingFileField(
        max_length=255,
        upload_to=get_local_file_path,
        null=True,
        blank=True,
        default=None,
        storage=stack_storage)

    # Where on disk is the custom pillar file for custom configuration for
    # all salt states used by the top file
    global_pillar_file = DeletingFileField(
        max_length=255,
        upload_to=get_local_file_path,
        null=True,
        blank=True,
        default=None,
        storage=stack_storage)

    # storage for properties file
    props_file = DeletingFileField(
        max_length=255,
        upload_to=get_local_file_path,
        null=True,
        blank=True,
        default=None,
        storage=stack_storage)

    # Use our custom manager object
    objects = StackQuerySet.as_manager()

    def __str__(self):
        return six.text_type('Stack {0} - {1}'.format(self.title, self.health))

    def log_history(self, message, activity=None):
        """
        Create a new history message and optionally set the activity on all hosts.
        :param message: the history message to create
        :param activity: the activity value to set on all hosts
        """
        if activity is not None:
            self.set_activity(activity)

        # Create a history
        self.history.create(message=message)

    def set_activity(self, activity):
        """
        Set the activity on all hosts in the stack
        :param activity: the activity to set
        """
        # Make sure all host activities are saved atomically
        with transaction.atomic(using=Stack.objects.db):
            self.activity = activity
            self.save()
            for host in self.hosts.all():
                host.activity = activity
                host.save()

    @property
    def volumes(self):
        return Volume.objects.filter(host__in=self.hosts.all())

    @django_cache('{ctype}-{id}-label-list')
    def get_cached_label_list(self):
        return self.labels.all()

    def get_driver_hosts_map(self, host_ids=None):
        """
        Stacks are comprised of multiple hosts. Each host may be
        located in different cloud accounts. This method returns
        a map of the underlying driver implementation and the hosts
        that running in the account.

        @param host_ids (list); a list of primary keys for the hosts
            we're interested in
        @returns (dict); each key is a provider driver implementation
            with QuerySet value for the matching host objects
        """
        host_queryset = self.get_hosts(host_ids)

        # Create an account -> hosts map
        accounts = {}
        for h in host_queryset:
            accounts.setdefault(h.cloud_account, []).append(h)

        # Convert to a driver -> hosts map
        result = {}
        for account, hosts in accounts.items():
            result[account.get_driver()] = host_queryset.filter(id__in=[h.id for h in hosts])

        return result

    @django_cache('stack-{id}-hosts')
    def get_cached_hosts(self):
        return self.hosts.all()

    @django_cache('stack-{id}-host-count')
    def host_count(self):
        return self.hosts.count()

    @django_cache('stack-{id}-volume-count')
    def volume_count(self):
        return self.volumes.count()

    def get_hosts(self, host_ids=None):
        """
        Quick way of getting all hosts or a subset for this stack.

        @host_ids (list); list of primary keys of hosts in this stack
        @returns (QuerySet);
        """
        if not host_ids:
            return self.hosts.all()
        return self.hosts.filter(id__in=host_ids)

    def get_formulas(self):
        return self.blueprint.get_formulas()

    def get_tags(self):
        tags = {}
        for label in self.labels.all():
            tags[label.key] = label.value

        tags['stack_id'] = self.id

        # No name allowed.  salt-cloud uses this and it would break everything.
        if 'Name' in tags:
            del tags['Name']

        return tags

    def _get_properties(self):
        if not self.props_file:
            return {}
        with open(self.props_file.path, 'r') as f:
            return json.load(f)

    def _set_properties(self, props):
        props_json = json.dumps(props, indent=4)
        if not self.props_file:
            self.props_file.save('stack.props', ContentFile(props_json))
        else:
            with open(self.props_file.path, 'w') as f:
                f.write(props_json)

    properties = property(_get_properties, _set_properties)

    @property
    def health(self):
        """
        Calculates the health of this stack from its hosts
        """
        healths = []
        activities = set()

        for host in self.get_cached_hosts():
            healths.append(host.health)
            activities.add(host.activity)

        if Activity.DEAD in activities:
            return Health.UNKNOWN if len(activities) == 1 else Health.UNHEALTHY

        return Health.aggregate(healths)

    def set_all_component_statuses(self, status):
        """
        Will set the status for all components on all hosts to the given status
        :param status: the status to set to
        :return:
        """
        for host in self.hosts.all():
            for component in host.formula_components.all():
                current_health = host.get_metadata_for_component(component).health
                host.component_metadatas.create(formula_component=component,
                                                status=status,
                                                current_health=current_health)

    def set_component_status(self, sls_path, status, include_list=None, exclude_list=None):
        """
        Will set the status for all hosts for the sls_path to be `status`,
        except anything in failed_hosts will be set to "failed".
        :param sls_path: The sls_path to set the status on
        :param status: The status to set to
        :param include_list: The hosts that need to be set.  If None, defaults to all hosts
        :param exclude_list: The hosts to be excluded.  If None, nothing is excluded
        :return:
        """
        include_list = include_list or []
        exclude_list = exclude_list or []

        for host in self.hosts.all():
            # If we have an include list, and the host isn't in it, skip it
            if include_list and host.hostname not in include_list:
                continue
            # if the host is in the exclude list, skip it
            if host.hostname in exclude_list:
                continue

            for component in host.formula_components.all():
                if component.sls_path == sls_path:
                    current_health = host.get_metadata_for_component(component).health
                    host.component_metadatas.create(formula_component=component,
                                                    status=status,
                                                    current_health=current_health)

    def create_security_groups(self):
        for hostdef in self.blueprint.host_definitions.all():

            # create the managed security group for each host definition
            # and assign the rules to the group
            sg_name = 'stackdio-managed-{0}-stack-{1}'.format(
                hostdef.slug,
                self.pk
            )
            sg_description = 'stackd.io managed security group'

            # cloud account and driver for the host definition
            account = hostdef.cloud_image.account

            if not account.create_security_groups:
                logger.info('Skipping creation of {0} because security group creation is turned '
                            'off for the account'.format(sg_name))
                continue

            driver = account.get_driver()

            try:

                sg_id = driver.create_security_group(sg_name,
                                                     sg_description,
                                                     delete_if_exists=True)
            except GroupExistsException as e:
                err_msg = 'Error creating security group: {0}'.format(e)
                raise APIException({'error': err_msg})

            logger.debug('Created security group {0}: {1}'.format(
                sg_name,
                sg_id
            ))

            for access_rule in hostdef.access_rules.all():
                driver.authorize_security_group(sg_id, {
                    'protocol': access_rule.protocol,
                    'from_port': access_rule.from_port,
                    'to_port': access_rule.to_port,
                    'rule': access_rule.rule,
                })

            # create the security group object that we can use for tracking
            self.security_groups.create(
                account=account,
                blueprint_host_definition=hostdef,
                name=sg_name,
                description=sg_description,
                group_id=sg_id,
                is_managed=True
            )

    def create_hosts(self, host_definition=None, count=None, backfill=False):
        """
        Creates host objects on this Stack. If no arguments are given, then
        all hosts available based on the Stack's blueprint host definitions
        will be created. If args are given, then only the `count` for the
        given `host_definition` will be created.

        @param host_definition (BlueprintHostDefinition object); the host
            definition to use for creating new hosts. If None, all host
            definitions for the stack's blueprint will be used.
        @param count (int); the number of hosts to create. If None, all
            hosts will be created.
        @param backfill (bool); If True, then hosts will be created with
            hostnames that fill in any gaps if necessary. If False, then
            hostnames will start at the end of the host list. This is only
            used when `host_definition` and `count` arguments are provided.
        """

        created_hosts = []

        if host_definition is None:
            host_definitions = self.blueprint.host_definitions.all()
        else:
            host_definitions = [host_definition]

        for hostdef in host_definitions:
            hosts = self.hosts.all()

            if count is None:
                start = 0
                end = hostdef.count
                indexes = range(start, end)
            elif not hosts:
                start = 0
                end = count
                indexes = range(start, end)
            else:
                if backfill:
                    hosts = hosts.order_by('index')

                    # The set of existing host indexes
                    host_indexes = set([h.index for h in hosts])

                    # The last index available
                    last_index = sorted(host_indexes)[-1]

                    # The set of expected indexes based on the last known
                    # index
                    expected_indexes = set(range(last_index + 1))

                    # Any gaps any the expected indexes?
                    gaps = expected_indexes - host_indexes

                    indexes = []
                    if gaps:
                        indexes = list(gaps)

                    count -= len(indexes)
                    start = sorted(host_indexes)[-1] + 1
                    end = start + count
                    indexes += range(start, end)
                else:
                    start = hosts.order_by('-index')[0].index + 1
                    end = start + count
                    indexes = range(start, end)

            # iterate over the host definition count and create individual
            # host records on the stack
            for i in indexes:
                hostname = hostdef.hostname_template.format(
                    namespace=self.namespace,
                    index=i
                )

                kwargs = dict(
                    index=i,
                    cloud_image=hostdef.cloud_image,
                    blueprint_host_definition=hostdef,
                    instance_size=hostdef.size,
                    hostname=hostname,
                    sir_price=hostdef.spot_price,
                    extra_options=hostdef.extra_options,
                )

                if hostdef.cloud_image.account.vpc_enabled:
                    kwargs['subnet_id'] = hostdef.subnet_id
                else:
                    kwargs['availability_zone'] = hostdef.zone

                host = self.hosts.create(**kwargs)

                account = host.cloud_account

                # Add in the cloud account default security groups as
                # defined by an admin.
                account_groups = set(list(
                    account.security_groups.filter(
                        is_default=True
                    )
                ))

                host.security_groups.add(*account_groups)

                if account.create_security_groups:
                    # Add in the security group provided by this host definition,
                    # but only if this functionality is enabled on the account
                    security_group = SecurityGroup.objects.get(
                        stack=self,
                        blueprint_host_definition=hostdef
                    )
                    host.security_groups.add(security_group)

                for volumedef in hostdef.volumes.all():
                    host.volumes.create(blueprint_volume=volumedef)

                for component in host.formula_components.all():
                    host.component_metadatas.create(formula_component=component)

                created_hosts.append(host)

        return created_hosts

    def generate_cloud_map(self):
        # TODO: Figure out a way to make this provider agnostic

        # TODO: Should we store this somewhere instead of assuming

        master = settings.STACKDIO_CONFIG.salt_master_fqdn

        images = collections.defaultdict(dict)

        hosts = self.hosts.all()
        cluster_size = len(hosts)

        for host in hosts:
            # load provider yaml to extract default security groups
            cloud_account = host.cloud_account
            cloud_account_yaml = yaml.safe_load(cloud_account.yaml)[cloud_account.slug]

            # pull various stuff we need for a host
            roles = [c.sls_path for c in host.formula_components.all()]
            instance_size = host.instance_size.title
            security_groups = set(sg.group_id for sg in host.security_groups.all())
            volumes = host.volumes.all()

            domain = cloud_account_yaml['append_domain']
            fqdn = '{0}.{1}'.format(host.hostname, domain)

            # The volumes will be defined on the map as well as in the grains.
            # Those in the map are used by salt-cloud to create and attach
            # the volumes (using the snapshot), whereas those on the grains
            # are available for states and modules to play with (e.g., to
            # mount the devices)
            map_volumes = []
            for vol in volumes:
                if vol.snapshot:
                    fstype = vol.snapshot.filesystem_type
                else:
                    fstype = DEFAULT_FILESYSTEM_TYPE

                v = {
                    'device': vol.device,
                    'mount_point': vol.mount_point,
                    'filesystem_type': fstype,
                    'create_fs': False,
                    'type': 'gp2',
                    'encrypted': vol.encrypted,
                }

                # Set the appropriate volume attribute
                if vol.volume_id:
                    v['volume_id'] = vol.volume_id
                elif vol.snapshot:
                    v['snapshot'] = vol.snapshot.snapshot_id
                else:
                    v['size'] = vol.size_in_gb
                    # This should be the only time we need to create the FS
                    v['create_fs'] = True

                # Update with the extra_options
                v.update(vol.extra_options)

                map_volumes.append(v)

            host_metadata = {
                'name': host.hostname,
                # The parameters in the minion dict will be passed on
                # to the minion and set in its default configuration
                # at /etc/salt/minion. This is where you would override
                # any default values set by salt-minion
                'minion': {
                    'master': master,
                    'log_level': 'debug',
                    'log_level_logfile': 'debug',
                    'mine_functions': {
                        'grains.items': []
                    },

                    # Grains are very useful when you need to set some
                    # static information about a machine (e.g., what stack
                    # id its registered under or how many total machines
                    # are in the cluster)
                    'grains': {
                        'roles': roles,
                        'stack_id': int(self.pk),
                        'fqdn': fqdn,
                        'domain': domain,
                        'cluster_size': cluster_size,
                        'stack_pillar_file': self.pillar_file.path,
                        'volumes': map_volumes,
                        'cloud_account': host.cloud_account.slug,
                        'cloud_image': host.cloud_image.slug,
                        'namespace': self.namespace,
                    },
                },

                # The rest of the settings in the map are salt-cloud
                # specific and control the VM in various ways
                # depending on the cloud account being used.
                'size': instance_size,
                'securitygroupid': list(security_groups),
                'volumes': map_volumes,
                'delvol_on_destroy': True,
                'del_all_vols_on_destroy': True,
            }

            if cloud_account.vpc_enabled:
                host_metadata['subnetid'] = host.subnet_id
            else:
                host_metadata['availability_zone'] = host.availability_zone.title

            # Add in spot instance config if needed
            if host.sir_price:
                host_metadata['spot_config'] = {
                    'spot_price': six.text_type(host.sir_price)  # convert to string
                }

            # Set our extra options - as long as they're not in the blacklist
            for key, value in host.extra_options.items():
                if key not in INSTANCE_OPTION_BLACKLIST:
                    host_metadata[key] = value

            images[host.cloud_image.slug][host.hostname] = host_metadata

        return images

    def generate_map_file(self):
        images = self.generate_cloud_map()

        map_file_yaml = yaml.safe_dump(images, default_flow_style=False)

        if not self.map_file:
            self.map_file.save('stack.map', ContentFile(map_file_yaml))
        else:
            with open(self.map_file.path, 'w') as f:
                f.write(map_file_yaml)

    def generate_top_file(self):
        top_file_data = {
            'base': {
                'G@stack_id:{0}'.format(self.pk): [
                    {'match': 'compound'},
                    'core.*',
                ]
            }
        }

        top_file_yaml = yaml.safe_dump(top_file_data, default_flow_style=False)

        if not self.top_file:
            self.top_file.save('stack_{0}_top.sls'.format(self.pk), ContentFile(top_file_yaml))
        else:
            with open(self.top_file.path, 'w') as f:
                f.write(top_file_yaml)

    def generate_orchestrate_file(self):
        hosts = self.hosts.all()
        stack_target = 'G@stack_id:{0}'.format(self.pk)

        def _matcher(sls_set):
            return ' and '.join(
                [stack_target] + ['G@roles:{0}'.format(i) for i in sls_set]
            )

        groups = {}
        for host in hosts:
            for component in host.formula_components.all():
                groups.setdefault(component.order, set()).add(component.sls_path)

        orchestrate = {}
        for order in sorted(groups):
            for role in groups[order]:
                orchestrate[role] = {
                    'salt.state': [
                        {'tgt': _matcher([role])},
                        {'tgt_type': 'compound'},
                        {'sls': role},
                    ]
                }
                depend = order - 1
                while depend >= 0:
                    if depend in groups.keys():
                        orchestrate[role]['salt.state'].append(
                            {'require': [{'salt': req} for req in groups[depend]]}
                        )
                        break
                    depend -= 1

        yaml_data = yaml.safe_dump(orchestrate, default_flow_style=False)

        if not self.orchestrate_file:
            self.orchestrate_file.save('orchestrate.sls', ContentFile(yaml_data))
        else:
            with open(self.orchestrate_file.path, 'w') as f:
                f.write(yaml_data)

    def generate_global_orchestrate_file(self):
        accounts = set([host.cloud_account for host in self.hosts.all()])

        orchestrate = {}

        for account in accounts:
            # Target the stack_id and cloud account
            target = 'G@stack_id:{0} and G@cloud_account:{1}'.format(
                self.id,
                account.slug)

            groups = {}
            for component in account.formula_components.all():
                groups.setdefault(component.order, set()).add(component.sls_path)

            for order in sorted(groups):
                for role in groups[order]:
                    state_title = '{0}_{1}'.format(account.slug, role)
                    orchestrate[state_title] = {
                        'salt.state': [
                            {'tgt': target},
                            {'tgt_type': 'compound'},
                            {'sls': role},
                        ]
                    }
                    depend = order - 1
                    while depend >= 0:
                        if depend in groups.keys():
                            orchestrate[role]['salt.state'].append(
                                {'require': [{'salt': req} for req in groups[depend]]}
                            )
                            break
                        depend -= 1

        yaml_data = yaml.safe_dump(orchestrate, default_flow_style=False)

        if not self.global_orchestrate_file:
            self.global_orchestrate_file.save('global_orchestrate.sls', ContentFile(yaml_data))
        else:
            with open(self.global_orchestrate_file.path, 'w') as f:
                f.write(yaml_data)

    def generate_pillar_file(self, update_formulas=False):
        # Import here to not cause circular imports
        from stackdio.api.formulas.models import FormulaVersion
        from stackdio.api.formulas.tasks import update_formula

        users = []
        # pull the create_ssh_users property from the stackd.io config file.
        # If it's False, we won't create ssh users on the box.
        if self.create_users:
            user_permissions_map = get_users_with_perms(
                self, attach_perms=True, with_superusers=True, with_group_users=True
            )

            for user, perms in user_permissions_map.items():
                if 'ssh_stack' in perms:
                    if user.settings.public_key:
                        logger.debug('Granting {0} ssh permission to stack: {1}'.format(
                            user.username,
                            self.title,
                        ))
                        users.append({
                            'username': user.username,
                            'public_key': user.settings.public_key,
                            'id': user.id,
                        })
                    else:
                        logger.debug(
                            'User {0} has ssh permission for stack {1}, but has no public key.  '
                            'Skipping.'.format(
                                user.username,
                                self.title,
                            )
                        )

        pillar_props = {
            '__stackdio__': {
                'users': users
            }
        }

        # If any of the formulas we're using have default pillar
        # data defined in its corresponding SPECFILE, we need to pull
        # that into our stack pillar file.

        # First get the unique set of formulas
        formulas = set()
        for host in self.hosts.all():
            formulas.update([c.formula for c in host.formula_components.all()])

        # for each unique formula, pull the properties from the SPECFILE
        for formula in formulas:
            # Grab the formula version
            try:
                version = self.formula_versions.get(formula=formula).version
            except FormulaVersion.DoesNotExist:
                version = formula.default_version

            if update_formulas:
                # Update the formulas if requested
                update_formula.si(formula.id, version)()
            recursive_update(pillar_props, formula.properties(version))

        # Add in properties that were supplied via the blueprint and during
        # stack creation
        recursive_update(pillar_props, self.properties)

        pillar_file_yaml = yaml.safe_dump(pillar_props, default_flow_style=False)

        if not self.pillar_file:
            self.pillar_file.save('stack.pillar', ContentFile(pillar_file_yaml))
        else:
            with open(self.pillar_file.path, 'w') as f:
                f.write(pillar_file_yaml)

    def generate_global_pillar_file(self, update_formulas=False):
        # Import here to not cause circular imports
        from stackdio.api.formulas.models import FormulaVersion
        from stackdio.api.formulas.tasks import update_formula

        pillar_props = {}

        # Find all of the globally used formulas for the stack
        accounts = set(
            [host.cloud_account for
             host in self.hosts.all()]
        )
        global_formulas = []
        for account in accounts:
            global_formulas.extend(account.get_formulas())

        # for each unique formula, pull the properties from the SPECFILE
        for formula in set(global_formulas):
            # Grab the formula version
            try:
                version = self.formula_versions.get(formula=formula).version
            except FormulaVersion.DoesNotExist:
                version = formula.default_version

            if update_formulas:
                # Update the formulas if requested
                update_formula.si(formula.id, version)()
            recursive_update(pillar_props, formula.properties(version))

        # Add in the account properties AFTER the stack properties
        for account in accounts:
            recursive_update(pillar_props,
                             account.global_orchestration_properties)

        pillar_file_yaml = yaml.safe_dump(pillar_props, default_flow_style=False)

        if not self.global_pillar_file:
            self.global_pillar_file.save('stack.global_pillar', ContentFile(pillar_file_yaml))
        else:
            with open(self.global_pillar_file.path, 'w') as f:
                f.write(pillar_file_yaml)

    def query_hosts(self, force=False):
        """
        Uses salt-cloud to query all the hosts for the given stack id.
        """
        CACHE_KEY = 'salt-cloud-full-query'

        cached_result = cache.get(CACHE_KEY)

        if cached_result and not force:
            logger.debug('salt-cloud query result cached')
            result = cached_result
        else:
            logger.debug('salt-cloud query result not cached, retrieving')
            logger.info('get_hosts_info: {0!r}'.format(self))

            salt_cloud = salt.cloud.CloudClient(settings.STACKDIO_CONFIG.salt_cloud_config)
            result = salt_cloud.full_query()

            # Cache the result for a minute
            cache.set(CACHE_KEY, result, 60)

        # yaml_result contains all host information in the stack, but
        # we have to dig a bit to get individual host metadata out
        # of account and provider type dictionaries
        host_result = {}
        for host in self.hosts.all():
            account = host.cloud_account
            provider = host.cloud_provider

            # each host is buried in a cloud provider type dict that's
            # inside a cloud account name dict

            # Grab the list of hosts
            host_map = result.get(account.slug, {}).get(provider.name, {})

            # Grab the individual host
            host_result[host.hostname] = host_map.get(host.hostname, None)

        return host_result

    def get_root_directory(self):
        return os.path.join(stack_storage.location, '{0}-{1}'.format(self.pk, self.slug))

    def get_log_directory(self):
        root_dir = self.get_root_directory()
        log_dir = os.path.join(root_dir, 'logs')
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        return log_dir

    def get_security_groups(self):
        return SecurityGroup.objects.filter(is_managed=True,
                                            hosts__stack=self).distinct()

    def get_role_list(self):
        roles = set()
        for bhd in self.blueprint.host_definitions.all():
            for formula_component in bhd.formula_components.all():
                roles.add(formula_component.sls_path)
        return list(roles)


@six.python_2_unicode_compatible
class StackHistory(TimeStampedModel):
    class Meta:
        verbose_name_plural = 'stack history'
        ordering = ['-created', '-id']

        default_permissions = ()

    stack = models.ForeignKey('Stack', related_name='history')

    message = models.CharField('Message', max_length=256)

    def __str__(self):
        return six.text_type('{} on {}'.format(self.message, self.stack))


@six.python_2_unicode_compatible
class StackCommand(TimeStampedModel, StatusModel):
    WAITING = 'waiting'
    RUNNING = 'running'
    FINISHED = 'finished'
    ERROR = 'error'
    STATUS = Choices(WAITING, RUNNING, FINISHED, ERROR)

    class Meta:
        verbose_name_plural = 'stack actions'

        default_permissions = ()

    stack = models.ForeignKey('Stack', related_name='commands')

    # The started executing
    start = models.DateTimeField('Start Time', blank=True, default=now)

    # Which hosts we want to target
    host_target = models.CharField('Host Target', max_length=255)

    # The command to be run (for custom actions)
    command = models.TextField('Command')

    # The output from the action
    std_out_storage = models.TextField()

    # The error output from the action
    std_err_storage = models.TextField()

    def __str__(self):
        return six.text_type('{} on {}'.format(self.command, self.host_target))

    @property
    def std_out(self):
        if self.std_out_storage != "":
            return json.loads(self.std_out_storage)
        else:
            return []

    @property
    def std_err(self):
        return self.std_err_storage

    @property
    def submit_time(self):
        return self.created

    @property
    def start_time(self):
        if self.status in (self.RUNNING, self.FINISHED):
            return self.start
        else:
            return ''

    @property
    def finish_time(self):
        if self.status == self.FINISHED:
            return self.modified
        else:
            return ''


@six.python_2_unicode_compatible
class Host(TimeStampedModel):
    class Meta:
        ordering = ['blueprint_host_definition', '-index']

        default_permissions = ()

    activity = models.CharField('Activity',
                                max_length=32,
                                blank=True,
                                choices=Activity.ALL,
                                default=Activity.QUEUED)

    stack = models.ForeignKey('Stack',
                              related_name='hosts')

    blueprint_host_definition = models.ForeignKey(
        'blueprints.BlueprintHostDefinition',
        related_name='hosts')

    hostname = models.CharField('Hostname', max_length=64)

    index = models.IntegerField('Index')

    security_groups = models.ManyToManyField('cloud.SecurityGroup',
                                             related_name='hosts')

    # The machine state as provided by the cloud account
    # Would like to have choices, but these vary per cloud provider
    # This is hidden from the user - only used internally
    state = models.CharField('State', max_length=32, default='unknown')

    # This must be updated automatically after the host is online.
    # After salt-cloud has launched VMs, we will need to look up
    # the DNS name set by whatever cloud provider is being used
    # and set it here
    provider_public_dns = models.CharField('Provider Public DNS', max_length=64, null=True)
    provider_public_ip = models.GenericIPAddressField('Provider Public IP', blank=True, null=True)
    provider_private_dns = models.CharField('Provider Private DNS', max_length=64, null=True)
    provider_private_ip = models.GenericIPAddressField('Provider Private IP', blank=True, null=True)

    # The FQDN for the host. This includes the hostname and the
    # domain if it was registered with DNS
    fqdn = models.CharField('FQDN', max_length=255, blank=True)

    # Instance id of the running host. This is provided by the cloud
    # provider
    instance_id = models.CharField('Instance ID', max_length=32, blank=True)

    # Spot instance request ID will be populated when metadata is refreshed
    # if the host has been configured to launch spot instances. By default,
    # it will be unknown and will be set to NA if spot instances were not
    # used.
    sir_id = models.CharField('SIR ID',
                              max_length=32,
                              default='unknown')

    # The spot instance price for this host if using spot instances
    sir_price = models.DecimalField('Spot Price',
                                    max_digits=5,
                                    decimal_places=2,
                                    null=True)

    # Any extra options we need to pass on to the host
    extra_options = JSONField('Extra Options')

    def __str__(self):
        return six.text_type(self.hostname)

    def set_activity(self, activity):
        self.activity = activity
        self.save()

    @property
    def health(self):
        """
        Calculates the health of this host from its component healths
        """
        # Get all the healths of the components
        healths = self.get_current_component_healths().values()

        # Add the health from the driver
        healths.append(self.get_driver().get_health_from_state(self.state))

        # Aggregate them together
        return Health.aggregate(healths)

    def get_current_component_healths(self):
        """
        Get a map of component -> current health
        """

        # Build all the cache keys first
        cache_key_map = {}
        for component in self.formula_components:
            cache_key = 'host-{}-component-health-for-{}'.format(self.id, component.sls_path)
            cache_key_map[cache_key] = component

        # Then grab them all from the cache at once
        cached_healths = cache.get_many(cache_key_map.keys())

        # Keep track of healths we need to put back in the cache
        healths_to_cache = {}

        # Keep track of the healths we need to return
        healths = {}

        for cache_key, component in cache_key_map.items():
            cached_health = cached_healths.get(cache_key)

            if cached_health is None:
                logger.debug('{} is not cached, getting health'.format(cache_key))
                cached_health = self.get_metadata_for_component(component).health

                # Add it to the healths we need to cache
                healths_to_cache[cache_key] = cached_health

            # Add it to the health map
            healths[component] = cached_health

        # Cache the healths forever - we'll invalidate the cache when the health is updated
        if healths_to_cache:
            cache.set_many(healths_to_cache, None)

        return healths

    def get_metadata_for_component(self, component):
        """
        Get the current status of a given component
        """
        if isinstance(component, six.string_types):
            sls_path = component
        elif hasattr(component, 'sls_path'):
            sls_path = component.sls_path
        else:
            raise ValueError('get_metadata_for_component requires a string or a '
                             'FormulaComponent object.')

        return self.component_metadatas.filter(
            formula_component__sls_path=sls_path
        ).order_by('-modified').first()

    @property
    def provider_metadata(self):
        metadata = self.stack.query_hosts()
        return metadata[self.hostname]

    @property
    @lru_cache()
    def formula_components(self):
        return self.blueprint_host_definition.formula_components.all()

    @property
    @lru_cache()
    def instance_size(self):
        return self.blueprint_host_definition.size

    @property
    def availability_zone(self):
        return self.blueprint_host_definition.zone

    @property
    def subnet_id(self):
        return self.blueprint_host_definition.subnet_id

    @property
    @lru_cache()
    def cloud_image(self):
        return self.blueprint_host_definition.cloud_image

    @property
    @lru_cache()
    def cloud_account(self):
        return self.cloud_image.account

    @property
    @lru_cache()
    def cloud_provider(self):
        return self.cloud_account.provider

    @lru_cache()
    def get_driver(self):
        return self.cloud_account.get_driver()


class ComponentMetadataQuerySet(models.QuerySet):

    def create(self, **kwargs):
        current_health = kwargs.pop('current_health', None)
        if 'status' in kwargs:
            kwargs['health'] = ComponentMetadata.HEALTH_MAP[kwargs['status']] \
                               or current_health \
                               or Health.UNKNOWN
        return super(ComponentMetadataQuerySet, self).create(**kwargs)


@six.python_2_unicode_compatible
class ComponentMetadata(TimeStampedModel):

    HEALTH_MAP = {
        ComponentStatus.QUEUED: None,
        ComponentStatus.RUNNING: Health.UNSTABLE,
        ComponentStatus.SUCCEEDED: Health.HEALTHY,
        ComponentStatus.FAILED: Health.UNHEALTHY,
        ComponentStatus.CANCELLED: None,
        ComponentStatus.UNKNOWN: Health.UNKNOWN,
    }

    STATUS_CHOICES = tuple((x, x) for x in set(HEALTH_MAP.keys()))
    HEALTH_CHOICES = tuple((x, x) for x in set(HEALTH_MAP.values()) if x is not None)

    # Fields
    formula_component = models.ForeignKey('formulas.FormulaComponent', related_name='metadatas')

    host = models.ForeignKey('Host', related_name='component_metadatas')

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
        return six.text_type('Component {} for host {} - {} ({})'.format(
            self.sls_path,
            self.host.hostname,
            self.status,
            self.health,
        ))

    @property
    @django_cache('component-metadata-{id}-sls-path')
    def sls_path(self):
        return self.formula_component.sls_path

    def set_status(self, status):
        # Make sure it's a valid status
        assert status in self.HEALTH_MAP

        self.status = status

        # Set the health based on the new status
        new_health = self.HEALTH_MAP[status]

        if new_health is not None:
            self.health = new_health

        self.save()


@receiver(models.signals.post_save, sender=ComponentMetadata)
def metadata_post_save(sender, **kwargs):
    """
    Catch the post_save signal for all ComponentMetadata
    objects and add the health to the cache
    """
    metadata = kwargs.pop('instance')

    host_id = metadata.host_id
    sls_path = metadata.sls_path

    logger.debug('Pre-caching health for component: {}'.format(metadata))

    # Go ahead and add this health to the cache - if it is being created,
    # it is definitely the most recent (which is always what we want)
    cache_key = 'host-{}-component-health-for-{}'.format(host_id, sls_path)
    cache.set(cache_key, metadata.health, None)


@receiver([models.signals.post_save, models.signals.post_delete], sender=Host)
def host_post_save(sender, **kwargs):
    host = kwargs.pop('instance')

    # Delete from the cache
    cache_keys = [
        'stack-{}-hosts'.format(host.stack_id),
        'stack-{}-host-count'.format(host.stack_id),
        'stack-{}-volume-count'.format(host.stack_id),
    ]
    cache.delete_many(cache_keys)


@receiver([models.signals.post_save, models.signals.post_delete], sender=Stack)
def stack_post_save(sender, **kwargs):
    stack = kwargs.pop('instance')

    # Delete from the cache
    cache_keys = [
        'blueprint-{}-stack-count'.format(stack.blueprint_id),
    ]
    cache.delete_many(cache_keys)
