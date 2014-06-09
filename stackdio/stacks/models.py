import json
import os
import re
import logging
import socket

from django.conf import settings
from django.db import models, transaction
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

import envoy
import yaml

from django_extensions.db.models import (
    TimeStampedModel,
    TitleSlugDescriptionModel,
)
import model_utils.models
from model_utils import Choices

from core.fields import DeletingFileField
from core.utils import recursive_update
from cloud.models import SecurityGroup
from volumes.models import Volume

PROTOCOL_CHOICES = [
    ('tcp', 'TCP'),
    ('udp', 'UDP'),
    ('icmp', 'ICMP'),
]

logger = logging.getLogger(__name__)

HOST_INDEX_PATTERN = re.compile('.*-.*-(\d+)')


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


# Map, pillar, and properties files go into storage
def get_map_file_path(obj, filename):
    return "stacks/{0}/{1}/stack.map".format(obj.owner.username, obj.slug)


def get_pillar_file_path(obj, filename):
    return "stacks/{0}/{1}/stack.pillar".format(obj.owner.username, obj.slug)


def get_props_file_path(obj, filename):
    return "stacks/{0}/{1}/stack.props".format(obj.owner.username, obj.slug)


# Top and overstate files go into salt root
def get_top_file_path(obj, filename):
    return "stack_{0}_top.sls".format(obj.id)


def get_overstate_file_path(obj, filename):
    return "stack_{0}_overstate.sls".format(obj.id)


class StackCreationException(Exception):
    def __init__(self, errors, *args, **kwargs):
        self.errors = errors
        super(StackCreationException, self).__init__(*args, **kwargs)


class Level(object):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARN = 'WARNING'
    ERROR = 'ERROR'


class StatusDetailModel(model_utils.models.StatusModel):
    status_detail = models.TextField(blank=True)

    class Meta:
        abstract = True

    def set_status(self, status, detail=''):
        self.status = status
        self.status_detail = detail
        return self.save()


class StackManager(models.Manager):

    @transaction.commit_on_success
    def create_stack(self, owner, blueprint, **data):
        '''
        '''
        title = data.get('title', '')
        description = data.get('description', '')
        public = data.get('public', False)

        if not title:
            raise ValueError("Stack 'title' is a required field.")

        stack = self.model(owner=owner,
                           blueprint=blueprint,
                           title=title,
                           description=description,
                           public=public)
        stack.save()

        # add the namespace
        namespace = data.get('namespace', '').strip()
        if not namespace:
            namespace = 'stack{0}'.format(stack.pk)
        stack.namespace = namespace
        stack.save()

        # manage the properties
        properties = blueprint.properties
        recursive_update(properties, data.get('properties', {}))
        props_json = json.dumps(properties, indent=4)
        if not stack.props_file:
            stack.props_file.save(stack.slug + '.props',
                                  ContentFile(props_json))
        else:
            with open(stack.props_file.path, 'w') as f:
                f.write(props_json)

        # create host records on the stack based on the host definitions in
        # the blueprint
        for hostdef in blueprint.host_definitions.all():

            # all components defined in the host definition
            components = hostdef.formula_components.all()

            # cloud provider and driver for the host definition
            cloud_provider = hostdef.cloud_profile.cloud_provider
            driver = cloud_provider.get_driver()

            # create the managed security group for each host definition
            # and assign the rules to the group
            sg_name = 'managed-{0}-{1}-stack-{2}'.format(
                owner.username,
                hostdef.slug,
                stack.pk)
            sg_description = 'stackd.io managed security group'
            sg_id = driver.create_security_group(sg_name,
                                                 sg_description,
                                                 delete_if_exists=True)

            for access_rule in hostdef.access_rules.all():
                driver.authorize_security_group(sg_name, {
                    'protocol': access_rule.protocol,
                    'from_port': access_rule.from_port,
                    'to_port': access_rule.to_port,
                    'rule': access_rule.rule,
                })

            # create a security group object that we can use for tracking
            security_group = SecurityGroup.objects.create(
                owner=owner,
                cloud_provider=cloud_provider,
                name=sg_name,
                description=sg_description,
                group_id=sg_id,
                is_managed=True
            )

            # iterate over the host definition count and create individual
            # host records on the stack
            for i in xrange(hostdef.count):
                hostname = hostdef.hostname_template.format(
                    namespace=stack.namespace,
                    username=owner.username,
                    index=i
                )

                kwargs = dict(
                    cloud_profile=hostdef.cloud_profile,
                    instance_size=hostdef.size,
                    hostname=hostname,
                    sir_price=hostdef.spot_price
                )

                if hostdef.cloud_profile.cloud_provider.vpc_enabled:
                    kwargs['subnet_id'] = hostdef.subnet_id
                else:
                    kwargs['availability_zone'] = hostdef.zone

                # Set blueprint host definition
                kwargs['blueprint_host_definition_id'] = hostdef.id

                host = stack.hosts.create(**kwargs)

                # Add in the cloud provider default security groups as
                # defined by an admin.
                provider_groups = set(list(
                    host.cloud_profile.cloud_provider.security_groups.filter(
                        is_default=True
                    )
                ))

                # set security groups
                host.security_groups.add(*provider_groups)
                host.security_groups.add(security_group)
                
                # add formula components
                host.formula_components.add(*components)

                for volumedef in hostdef.volumes.all():
                    logger.debug(volumedef)
                    logger.debug(stack)
                    logger.debug(host)
                    Volume.objects.create(
                        stack=stack,
                        host=host,
                        snapshot=volumedef.snapshot,
                        hostname=hostname,
                        device=volumedef.device,
                        mount_point=volumedef.mount_point
                    )

        # Generate configuration files for salt and salt-cloud
        # NOTE: The order is important here. pillar must be available before
        # the map file is rendered or else we'll miss important grains that
        # need to be set at launch time
        stack._generate_pillar_file()
        stack._generate_top_file()
        stack._generate_overstate_file()
        stack._generate_map_file()

        return stack


class Stack(TimeStampedModel, TitleSlugDescriptionModel):
    OK = 'ok'
    ERROR = 'error'
    PENDING = 'pending'
    SYNCING = 'syncing'
    STARTING = 'starting'
    LAUNCHING = 'launching'
    FINALIZING = 'finalizing'
    CONFIGURING = 'configuring'
    PROVISIONING = 'provisioning'
    EXECUTING_ACTION = 'executing_action'
    TERMINATING = 'terminating'
    DESTROYING = 'destroying'
    REBOOTING = 'rebooting'
    FINISHED = 'finished'
    STOPPING = 'stopping'
    RUNNING = 'running'

    class Meta:
        unique_together = ('owner', 'title')

    # The "owner" of the stack and all of its infrastructure
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='stacks')

    # What blueprint did this stack derive from?
    blueprint = models.ForeignKey('blueprints.Blueprint',
                                  related_name='stacks')

    # An arbitrary namespace for this stack. Mainly useful for Blueprint
    # hostname templates
    namespace = models.CharField(max_length=64, blank=True)

    # is this stack publicly available -- meaning it can be found by other
    # users and will remain in read-only mode to them
    public = models.BooleanField(default=False)

    # Where on disk is the salt-cloud map file stored
    map_file = DeletingFileField(
        max_length=255,
        upload_to=get_map_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    # Where on disk is the custom salt top.sls file stored
    top_file = DeletingFileField(
        max_length=255,
        upload_to=get_top_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(
            location=settings.STACKDIO_CONFIG.salt_core_states))

    # Where on disk is the custom overstate file stored
    overstate_file = DeletingFileField(
        max_length=255,
        upload_to=get_overstate_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(
            location=settings.STACKDIO_CONFIG.salt_core_states))

    # Where on disk is the custom pillar file for custom configuration for
    # all salt states used by the top file
    pillar_file = DeletingFileField(
        max_length=255,
        upload_to=get_pillar_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    # storage for properties file
    props_file = DeletingFileField(
        max_length=255,
        upload_to=get_props_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    # Use our custom manager object
    objects = StackManager()

    def __unicode__(self):
        return u'{0} (id={1})'.format(self.title, self.pk)

    def set_status(self, event, status, level=Level.INFO):
        self.history.create(event=event, status=status, level=level)

    def get_driver_hosts_map(self):
        '''
        Stacks are comprised of multiple hosts. Each host may be
        located in different cloud providers. This method returns
        a map of the underlying driver implementation and the hosts
        that running in the provider.
        '''
        providers = set()
        hosts = self.hosts.all()
        for host in hosts:
            providers.add(host.get_provider())

        result = {}
        for provider in providers:
            hosts = self.hosts.filter(cloud_profile__cloud_provider=provider)
            result[provider.get_driver()] = hosts
        return result

    def get_hosts(self, host_ids=None):
        '''
        Quick way of getting all hosts or a subset for this stack.
        '''
        if not host_ids:
            return self.hosts.all()
        return self.hosts.filter(id__in=host_ids)

    @property
    def properties(self):
        if not self.props_file:
            return {}
        with open(self.props_file.path) as f:
            return json.loads(f.read())

    @properties.setter
    def properties(self, props):
        properties = self.properties
        recursive_update(properties, props)
        props_json = json.dumps(properties, indent=4)
        if not self.props_file:
            self.props_file.save(self.slug + '.props', ContentFile(props_json))
        else:
            with open(self.props_file.path, 'w') as f:
                f.write(props_json)

    def _generate_map_file(self):
        # TODO: Figure out a way to make this provider agnostic

        # TODO: Should we store this somewhere instead of assuming
        # the master will always be this box?
        master = socket.getfqdn()

        profiles = {}

        hosts = self.hosts.all()
        cluster_size = len(hosts)

        for host in hosts:
            # load provider yaml to extract default security groups
            cloud_provider = host.cloud_profile.cloud_provider
            cloud_provider_yaml = yaml.safe_load(
                cloud_provider.yaml)[cloud_provider.slug]

            # pull various stuff we need for a host
            roles = [c.component.sls_path for
                     c in host.formula_components.all()]
            instance_size = host.instance_size.title
            security_groups = set([
                sg.group_id for sg in host.security_groups.all()
            ])
            volumes = host.volumes.all()

            fqdn = '{0}.{1}'.format(host.hostname,
                                    cloud_provider_yaml['append_domain'])

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
                    'filesystem_type': vol.snapshot.filesystem_type,
                }
                if vol.volume_id:
                    v['volume_id'] = vol.volume_id
                else:
                    v['snapshot'] = vol.snapshot.snapshot_id

                map_volumes.append(v)

            host_metadata = {
                host.hostname: {
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
                            'cluster_size': cluster_size,
                            'stack_pillar_file': self.pillar_file.path,
                            'volumes': map_volumes,
                        },
                    },

                    # The rest of the settings in the map are salt-cloud
                    # specific and control the VM in various ways
                    # depending on the cloud provider being used.
                    'size': instance_size,
                    'securitygroupid': list(security_groups),
                    'volumes': map_volumes,
                }
            }

            if cloud_provider.vpc_enabled:
                host_metadata[host.hostname]['subnetid'] = host.subnet_id
            else:
                host_metadata[host.hostname]['availability_zone'] \
                    = host.availability_zone.title

            # Add in spot instance config if needed
            if host.sir_price:
                host_metadata[host.hostname]['spot_config'] = {
                    'spot_price': str(host.sir_price)  # convert to string
                }

            profiles.setdefault(host.cloud_profile.slug, []) \
                .append(host_metadata)

        map_file_yaml = yaml.safe_dump(profiles,
                                       default_flow_style=False)

        if not self.map_file:
            self.map_file.save(self.slug + '.map', ContentFile(map_file_yaml))
        else:
            with open(self.map_file.path, 'w') as f:
                f.write(map_file_yaml)

    def _generate_top_file(self):
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
            self.top_file.save('stack_{0}_top.sls'.format(self.pk),
                               ContentFile(top_file_yaml))
        else:
            with open(self.top_file.path, 'w') as f:
                f.write(top_file_yaml)

    def _generate_overstate_file(self):
        hosts = self.hosts.all()
        stack_target = 'G@stack_id:{0}'.format(self.pk)

        def _matcher(sls_set):
            return ' and '.join(
                [stack_target] + ['G@roles:{0}'.format(i) for i in sls_set]
            )

        groups = {}
        for host in hosts:
            for c in host.formula_components.all():
                groups.setdefault(
                    c.order, set()
                ).add(c.component.sls_path)

        overstate = {}
        for order in sorted(groups.keys()):
            overstate['group_{0}'.format(order)] = {
                'match': _matcher(groups[order]),
                'sls': list(groups[order]),
            }

        yaml_data = yaml.safe_dump(overstate, default_flow_style=False)
        if not self.overstate_file:
            self.overstate_file.save(
                'stack_{0}_overstate.sls'.format(self.pk),
                ContentFile(yaml_data))
        else:
            with open(self.overstate_file.path, 'w') as f:
                f.write(yaml_data)

    def _generate_overstate_file_bak(self):
        hosts = self.hosts.all()

        # Get the unique set of components for this stack
        components = set()
        for host in hosts:
            components.update(list(
                host.formula_components.all().order_by('order')
            ))

        # build a data structure more suitable for helping us build
        # the overstate dict
        groups = {}
        for c in components:
            '''
            {
                order_0: {
                    host_0: [sls, sls, ...],
                    host_1: [sls, sls, ...],
                    ...
                },
                order_1: {
                    ...
                }
                ...
            }
            '''
            groups.setdefault(
                c.order, {}
            ).setdefault(
                '{0}-{1}'.format(c.order, c.host.slug), []
            ).append(
                c.component.sls_path
            )

        # now we know what order each defined blueprint host is in and
        # the corresponding components to be installed. We will match
        # hosts based on the stack_id and all roles/SLS. Each group of
        # hosts beyond the first will have a requirement on the group
        # before it
        overstate = {}
        for i in sorted(groups.keys()):
            for host, sls in groups[i].iteritems():
                matches = ' and '.join(['G@roles:{0}'.format(r) for r in sls])
                overstate[host] = {
                    'match': 'G@stack_id:{0} and {1}'.format(self.pk, matches),
                    'sls': sls
                }

                if i > 0:
                    overstate[host]['require'] = groups[i - 1].keys()

        # Dump the overstate dict into yaml for salt
        yaml_data = yaml.safe_dump(overstate, default_flow_style=False)
        if not self.overstate_file:
            self.overstate_file.save(
                'stack_{0}_overstate.sls'.format(self.pk),
                ContentFile(yaml_data))
        else:
            with open(self.overstate_file.path, 'w') as f:
                f.write(yaml_data)

    def _generate_pillar_file(self):
        from blueprints.models import BlueprintHostFormulaComponent

        pillar_props = {
            '__stackdio__': {
                'username': self.owner.username,
                'publickey': self.owner.settings.public_key,
            }
        }

        # If any of the formulas we're using have default pillar
        # data defined in its corresponding SPECFILE, we need to pull
        # that into our stack pillar file.

        # First get the unique set of formulas
        hosts = self.hosts.all()
        formulas = set(
            [c.component.formula for
             c in BlueprintHostFormulaComponent.objects.filter(
                 hosts__in=hosts)]
        )

        # for each unique formula, pull the properties from the SPECFILE
        for formula in formulas:
            recursive_update(pillar_props, formula.properties)

        # Add in properties that were supplied via the blueprint and during
        # stack creation
        recursive_update(pillar_props, self.properties)

        pillar_file_yaml = yaml.safe_dump(pillar_props,
                                          default_flow_style=False)

        if not self.pillar_file:
            self.pillar_file.save('{0}.pillar'.format(self.slug),
                                  ContentFile(pillar_file_yaml))
        else:
            with open(self.pillar_file.path, 'w') as f:
                f.write(pillar_file_yaml)

    def query_hosts(self):
        '''
        Uses salt-cloud to query all the hosts for the given stack id.
        '''
        try:
            if not self.map_file:
                return {}

            logger.info('get_hosts_info: {0!r}'.format(self))

            # salt-cloud command to pull host information with
            # a yaml output
            query_cmd = ' '.join([
                'salt-cloud',
                '--full-query',             # execute a full query
                '--out=yaml',               # output in yaml format
                '--config-dir={0}',         # salt config dir
                '--map={1}',                # map file to use
            ]).format(
                settings.STACKDIO_CONFIG.salt_config_root,
                self.map_file.path,
            )

            result = envoy.run(query_cmd)

            # Run the envoy stdout through the yaml parser. The format
            # will always be a dictionary with one key (the provider type)
            # and a value that's a dictionary containing keys for every
            # host in the stack.
            yaml_result = yaml.safe_load(result.std_out)

            if not yaml_result:
                return {}

            # yaml_result contains all host information in the stack, but
            # we have to dig a bit to get individual host metadata out
            # of provider and provider type dictionaries
            host_result = {}
            for host in self.hosts.all():
                cloud_provider = host.cloud_profile.cloud_provider
                provider_type = cloud_provider.provider_type

                # each host is buried in a cloud provider type dict that's
                # inside a cloud provider name dict
                host_result[host.hostname] = yaml_result \
                    .get(cloud_provider.slug, {}) \
                    .get(provider_type.type_name, {}) \
                    .get(host.hostname, None)

            return host_result

        except Exception:
            logger.exception('Unhandled exception')
            raise

    def get_root_directory(self):
        return os.path.dirname(self.map_file.path)

    def get_log_directory(self):
        log_dir = os.path.join(os.path.dirname(self.map_file.path), 'logs')
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        return log_dir

    def get_security_groups(self):
        groups = SecurityGroup.objects.filter(is_managed=True, 
                                              hosts__stack=self)
        ret = []
        for group in groups:
            if group not in ret:
                 ret.append(group)

        return ret

class StackHistory(TimeStampedModel):

    class Meta:
        verbose_name_plural = 'stack history'
        ordering = ['-created', '-id']

    stack = models.ForeignKey('Stack', related_name='history')

    # What 'event' (method name, task name, etc) that caused
    # this status update
    event = models.CharField(max_length=128)

    # The human-readable description of the event
    status = models.TextField(blank=True)

    # Optional: level (DEBUG, INFO, WARNING, ERROR, etc)
    level = models.CharField(max_length=16, choices=(
        (Level.DEBUG, Level.DEBUG),
        (Level.INFO, Level.INFO),
        (Level.WARN, Level.WARN),
        (Level.ERROR, Level.ERROR),
    ))


class Host(TimeStampedModel, StatusDetailModel):
    OK = 'ok'
    DELETING = 'deleting'
    STATUS = Choices(OK, DELETING)

    # TODO: We should be using generic foreign keys here to a cloud provider
    # specific implementation of a Host object. I'm not exactly sure how this
    # will work, but I think by using Django's content type system we can make
    # it work...just not sure how easy it will be to extend, maintain, etc.

    stack = models.ForeignKey('Stack',
                              related_name='hosts')

    cloud_profile = models.ForeignKey('cloud.CloudProfile',
                                      related_name='hosts')

    instance_size = models.ForeignKey('cloud.CloudInstanceSize',
                                      related_name='hosts')

    availability_zone = models.ForeignKey('cloud.CloudZone',
                                          null=True,
                                          related_name='hosts')

    subnet_id = models.CharField(max_length=32, blank=True, default='')

    blueprint_host_definition = models.ForeignKey(
        'blueprints.BlueprintHostDefinition',
        related_name='hosts')

    formula_components = models.ManyToManyField(
        'blueprints.BlueprintHostFormulaComponent',
        related_name='hosts')

    hostname = models.CharField(max_length=64)

    security_groups = models.ManyToManyField('cloud.SecurityGroup',
                                             related_name='hosts')

    # The machine state as provided by the cloud provider
    state = models.CharField(max_length=32, default='unknown')
    state_reason = models.CharField(max_length=255, default='', blank=True)

    # This must be updated automatically after the host is online.
    # After salt-cloud has launched VMs, we will need to look up
    # the DNS name set by whatever cloud provider is being used
    # and set it here
    provider_dns = models.CharField(max_length=64, blank=True)
    provider_private_dns = models.CharField(max_length=64, blank=True)
    provider_private_ip = models.CharField(max_length=64, blank=True)

    # The FQDN for the host. This includes the hostname and the
    # domain if it was registered with DNS
    fqdn = models.CharField(max_length=255, blank=True)

    # Instance id of the running host. This is provided by the cloud
    # provider
    instance_id = models.CharField(max_length=32, blank=True)

    # Spot instance request ID will be populated when metadata is refreshed
    # if the host has been configured to launch spot instances. By default,
    # it will be unknown and will be set to NA if spot instances were not
    # used.
    sir_id = models.CharField(max_length=32,
                              default='unknown')

    # The spot instance price for this host if using spot instances
    sir_price = models.DecimalField(max_digits=5,
                                    decimal_places=2,
                                    null=True)

    def __unicode__(self):
        return self.hostname

    def get_provider(self):
        return self.cloud_profile.cloud_provider

    def get_provider_type(self):
        return self.cloud_profile.cloud_provider.provider_type

    def get_driver(self):
        return self.cloud_profile.get_driver()
