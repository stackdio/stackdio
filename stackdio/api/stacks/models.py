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


import json
import logging
import os
import re
import socket

import salt.cloud
import yaml
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.cache import cache
from django.db import models, transaction
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.utils.timezone import now
from django_extensions.db.models import (
    TimeStampedModel,
    TitleSlugDescriptionModel,
)
from guardian.shortcuts import get_users_with_perms
from model_utils import Choices
from model_utils.models import StatusModel

from stackdio.core.fields import DeletingFileField
from stackdio.core.utils import recursive_update
from stackdio.api.cloud.models import SecurityGroup

PROTOCOL_CHOICES = [
    ('tcp', 'TCP'),
    ('udp', 'UDP'),
    ('icmp', 'ICMP'),
]

logger = logging.getLogger(__name__)

HOST_INDEX_PATTERN = re.compile(r'.*-.*-(\d+)')


def get_hostnames_from_hostdefs(hostdefs, username='', namespace=''):
    hostnames = []
    for hostdef in hostdefs:
        for i in xrange(hostdef.count):
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


class Level(object):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARN = 'WARNING'
    ERROR = 'ERROR'


class StatusDetailModel(StatusModel):
    status_detail = models.TextField(blank=True)

    class Meta:
        abstract = True

        default_permissions = ()

    def set_status(self, status, detail=''):
        self.status = status
        self.status_detail = detail
        return self.save()


class StackQuerySet(models.QuerySet):

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
    'start',
    'stop',
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


class Stack(TimeStampedModel, TitleSlugDescriptionModel, StatusModel):

    # Launch workflow:
    PENDING = 'pending'
    LAUNCHING = 'launching'
    CONFIGURING = 'configuring'
    SYNCING = 'syncing'
    PROVISIONING = 'provisioning'
    ORCHESTRATING = 'orchestrating'
    FINALIZING = 'finalizing'
    FINISHED = 'finished'

    # Delete workflow:
    # PENDING
    DESTROYING = 'destroying'
    # FINISHED

    # Other actions
    # LAUNCHING
    STARTING = 'starting'
    STOPPING = 'stopping'
    TERMINATING = 'terminating'
    EXECUTING_ACTION = 'executing_action'

    # Errors
    ERROR = 'error'

    SAFE_STATES = [FINISHED, ERROR]

    # Not sure?
    OK = 'ok'
    RUNNING = 'running'
    REBOOTING = 'rebooting'

    STATUS = Choices(PENDING, LAUNCHING, CONFIGURING, SYNCING, PROVISIONING,
                     ORCHESTRATING, FINALIZING, DESTROYING, FINISHED,
                     STARTING, STOPPING, TERMINATING, EXECUTING_ACTION, ERROR)

    model_permissions = _stack_model_permissions
    object_permissions = _stack_object_permissions
    searchable_fields = ('title', 'description', 'history__status_detail')

    class Meta:
        ordering = ('title',)

        default_permissions = tuple(set(_stack_model_permissions + _stack_object_permissions))

        unique_together = ('title',)

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

    def __unicode__(self):
        return u'{0} (id={1})'.format(self.title, self.id)

    def set_status(self, event, status, detail, level=Level.INFO):
        self.status = status
        self.save()
        self.history.create(event=event, status=status,
                            status_detail=detail, level=level)

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
            accounts.setdefault(h.get_account(), []).append(h)

        # Convert to a driver -> hosts map
        result = {}
        for account, hosts in accounts.items():
            result[account.get_driver()] = host_queryset.filter(id__in=[h.id for h in hosts])

        return result

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

    @property
    def properties(self):
        if not self.props_file:
            return {}
        with open(self.props_file.path, 'r') as f:
            return json.load(f)

    @properties.setter
    def properties(self, props):
        props_json = json.dumps(props, indent=4)
        if not self.props_file:
            self.props_file.save('stack.props', ContentFile(props_json))
        else:
            with open(self.props_file.path, 'w') as f:
                f.write(props_json)

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
                logger.debug('Skipping creation of {0} because security group creation is turned '
                             'off for the account'.format(sg_name))
                continue

            driver = account.get_driver()

            try:

                sg_id = driver.create_security_group(sg_name,
                                                     sg_description,
                                                     delete_if_exists=True)
            except Exception as e:
                err_msg = 'Error creating security group: {0}'.format(str(e))
                self.set_status('create_security_groups', self.ERROR,
                                err_msg, Level.ERROR)

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
                start, end = 0, hostdef.count
                indexes = range(start, end)
            elif not hosts:
                start, end = 0, count
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
                    indexes = xrange(start, end)

            # all components defined in the host definition
            components = hostdef.formula_components.all()

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
                    state=Host.PENDING
                )

                if hostdef.cloud_image.account.vpc_enabled:
                    kwargs['subnet_id'] = hostdef.subnet_id
                else:
                    kwargs['availability_zone'] = hostdef.zone

                host = self.hosts.create(**kwargs)

                account = host.cloud_image.account

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

                # add formula components
                host.formula_components.add(*components)

                for volumedef in hostdef.volumes.all():
                    self.volumes.create(
                        host=host,
                        snapshot=volumedef.snapshot,
                        hostname=hostname,
                        device=volumedef.device,
                        mount_point=volumedef.mount_point
                    )

                created_hosts.append(host)

        return created_hosts

    def generate_cloud_map(self):
        # TODO: Figure out a way to make this provider agnostic

        # TODO: Should we store this somewhere instead of assuming

        master = socket.getfqdn()

        images = {}

        hosts = self.hosts.all()
        cluster_size = len(hosts)

        for host in hosts:
            # load provider yaml to extract default security groups
            cloud_account = host.cloud_image.account
            cloud_account_yaml = yaml.safe_load(cloud_account.yaml)[cloud_account.slug]

            # pull various stuff we need for a host
            roles = [c.sls_path for c in host.formula_components.all()]
            instance_size = host.instance_size.title
            security_groups = set([
                sg.group_id for sg in host.security_groups.all()
            ])
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
                v = {
                    'device': vol.device,
                    'mount_point': vol.mount_point,
                    # filesystem_type doesn't matter, should remove soon
                    'filesystem_type': vol.snapshot.filesystem_type,
                    'type': 'gp2',
                }
                if vol.volume_id:
                    v['volume_id'] = vol.volume_id
                else:
                    v['snapshot'] = vol.snapshot.snapshot_id

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
                        'cloud_account': host.cloud_image.account.slug,
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
                    'spot_price': str(host.sir_price)  # convert to string
                }

            images.setdefault(host.cloud_image.slug, {})[host.hostname] = host_metadata

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
        for order in sorted(groups.keys()):
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
        accounts = set([host.cloud_image.account for host in self.hosts.all()])

        orchestrate = {}

        for account in accounts:
            # Target the stack_id and cloud account
            target = 'G@stack_id:{0} and G@cloud_account:{1}'.format(
                self.id,
                account.slug)

            groups = {}
            for component in account.formula_components.all():
                groups.setdefault(component.order, set()).add(component.sls_path)

            for order in sorted(groups.keys()):
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

        # Update the formulas if requested
        if update_formulas:
            for formula in formulas:
                # Update the formula, and fail silently if there was an error.
                if formula.private_git_repo:
                    logger.debug('Skipping private formula: {0}'.format(formula.uri))
                    continue

                try:
                    version = self.formula_versions.get(formula=formula).version
                except FormulaVersion.DoesNotExist:
                    version = formula.default_version

                update_formula.si(formula.id, None, version, raise_exception=False)()

        # for each unique formula, pull the properties from the SPECFILE
        for formula in formulas:
            recursive_update(pillar_props, formula.properties)

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
            [host.cloud_image.account for
                host in self.hosts.all()]
        )
        global_formulas = []
        for account in accounts:
            global_formulas.extend(account.get_formulas())

        # Update the formulas if requested
        if update_formulas:
            for formula in global_formulas:
                # Update the formula, and fail silently if there was an error.
                if formula.private_git_repo:
                    logger.debug('Skipping private formula: {0}'.format(formula.uri))
                    continue

                try:
                    version = self.formula_versions.get(formula=formula).version
                except FormulaVersion.DoesNotExist:
                    version = formula.default_version

                update_formula.si(formula.id, None, version, raise_exception=False)()

        # Add the global formulas into the props
        for formula in set(global_formulas):
            recursive_update(pillar_props, formula.properties)

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
            account = host.get_account()
            provider = account.provider

            # each host is buried in a cloud provider type dict that's
            # inside a cloud account name dict

            # Grab the list of hosts
            host_map = result.get(account.slug, {}).get(provider.name, {})

            # Grab the individual host
            host_result[host.hostname] = host_map.get(host.hostname, None)

        return host_result

    def get_root_directory(self):
        if self.map_file:
            return os.path.dirname(self.map_file.path)
        if self.props_file:
            return os.path.dirname(self.props_file.path)
        return None

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


class StackHistory(TimeStampedModel, StatusDetailModel):

    class Meta:
        verbose_name_plural = 'stack history'
        ordering = ['-created', '-id']

        default_permissions = ()

    STATUS = Stack.STATUS

    stack = models.ForeignKey('Stack', related_name='history')

    # What 'event' (method name, task name, etc) that caused
    # this status update
    event = models.CharField(max_length=128)

    # The human-readable description of the event
    # status = models.TextField(blank=True)

    # Optional: level (DEBUG, INFO, WARNING, ERROR, etc)
    level = models.CharField(max_length=16, choices=(
        (Level.DEBUG, Level.DEBUG),
        (Level.INFO, Level.INFO),
        (Level.WARN, Level.WARN),
        (Level.ERROR, Level.ERROR),
    ))


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


class Host(TimeStampedModel, StatusDetailModel):
    PENDING = 'pending'
    OK = 'ok'
    DELETING = 'deleting'
    STATUS = Choices(PENDING, OK, DELETING)

    class Meta:
        ordering = ['blueprint_host_definition', '-index']

        default_permissions = ()

    # TODO: We should be using generic foreign keys here to a cloud account
    # specific implementation of a Host object. I'm not exactly sure how this
    # will work, but I think by using Django's content type system we can make
    # it work...just not sure how easy it will be to extend, maintain, etc.

    stack = models.ForeignKey('Stack',
                              related_name='hosts')

    cloud_image = models.ForeignKey('cloud.CloudImage',
                                    related_name='hosts')

    instance_size = models.ForeignKey('cloud.CloudInstanceSize',
                                      related_name='hosts')

    availability_zone = models.ForeignKey('cloud.CloudZone',
                                          null=True,
                                          related_name='hosts')

    subnet_id = models.CharField('Subnet ID', max_length=32, blank=True, default='')

    blueprint_host_definition = models.ForeignKey(
        'blueprints.BlueprintHostDefinition',
        related_name='hosts')

    hostname = models.CharField('Hostname', max_length=64)

    index = models.IntegerField('Index')

    security_groups = models.ManyToManyField('cloud.SecurityGroup',
                                             related_name='hosts')

    # The machine state as provided by the cloud account
    state = models.CharField('State', max_length=32, default='unknown')
    state_reason = models.CharField('State Reason', max_length=255, default='', blank=True)

    # This must be updated automatically after the host is online.
    # After salt-cloud has launched VMs, we will need to look up
    # the DNS name set by whatever cloud provider is being used
    # and set it here
    provider_dns = models.CharField('Provider DNS', max_length=64, blank=True)
    provider_private_dns = models.CharField('Provider Private DNS', max_length=64, blank=True)
    provider_private_ip = models.CharField('Provider Private IP Address', max_length=64, blank=True)

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

    def __unicode__(self):
        return self.hostname

    @property
    def provider_metadata(self):
        metadata = self.stack.query_hosts()
        return metadata[self.hostname]

    @property
    def formula_components(self):
        return self.blueprint_host_definition.formula_components

    def get_account(self):
        return self.cloud_image.account

    def get_provider(self):
        return self.get_account().provider

    def get_driver(self):
        return self.cloud_image.get_driver()
