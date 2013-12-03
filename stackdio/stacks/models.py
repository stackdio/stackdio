import collections
import json
import os
import re
import logging
import socket
from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

import envoy
import yaml

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel
import model_utils.models 
from model_utils import Choices

from core.fields import DeletingFileField
from cloud.models import (
    CloudProvider,
    CloudProfile,
    CloudZone,
    CloudInstanceSize,
    SecurityGroup
)
from volumes.models import Volume

logger = logging.getLogger(__name__)

HOST_INDEX_PATTERN = re.compile('.*-.*-(\d+)')

# Thanks Alex Martelli
# http://goo.gl/nENTTt
def recursive_update(d, u):
    '''
    Recursive update of one dictionary with another. The built-in
    python dict::update will erase exisitng values.
    '''
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = recursive_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d

def get_map_file_path(obj, filename):
    return "stacks/{0}/{1}.map".format(obj.owner.username, obj.slug)

def get_top_file_path(obj, filename):
    return "stack_{0}_top.sls".format(obj.id)

def get_overstate_file_path(obj, filename):
    return "stack_{0}_overstate.sls".format(obj.id)

def get_pillar_file_path(obj, filename):
    return "stacks/{0}/{1}.pillar".format(obj.owner.username, obj.slug)

def get_props_file_path(obj, filename):
    return "stacks/{0}/{1}.props".format(obj.owner.username, obj.slug)


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

        if not title:
            raise ValueError("Stack 'title' is a required field.")

        stack = self.model(owner=owner,
                           blueprint=blueprint,
                           title=title,
                           description=description)
        stack.save()

        # manage the properties
        properties = blueprint.properties
        recursive_update(properties, data.get('properties', {}))
        props_json = json.dumps(properties, indent=4)
        if not stack.props_file:
            stack.props_file.save(stack.slug+'.props', ContentFile(props_json))
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
            sg_name='{0}-{1}-stackdio-id-{2}'.format(
                hostdef.prefix,
                owner.username,
                stack.pk)
            sg_description='stackd.io managed security group'
            sg_id = driver.create_security_group(sg_name, sg_description)

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
                group_id=sg_id
            )

            # iterate over the host definition count and create individual
            # host records on the stack
            for i in xrange(1, hostdef.count+1):
                hostname = '{prefix}-{username}-{index}'.format(
                    prefix=hostdef.prefix,
                    username=owner.username,
                    index=i
                )
                host = stack.hosts.create(cloud_profile=hostdef.cloud_profile,
                                          instance_size=hostdef.size,
                                          availability_zone=hostdef.zone,
                                          hostname=hostname,
                                          sir_price=hostdef.spot_price)

                # Add in the cloud provider default security groups as 
                # defined by an admin.
                provider_groups = set(list(host.cloud_profile.cloud_provider.security_groups.filter(
                    is_default=True
                )))

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
    blueprint = models.ForeignKey('blueprints.Blueprint', related_name='stacks')

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
        storage=FileSystemStorage(location=settings.SALT_STATE_ROOT))

    # Where on disk is the custom overstate file stored
    overstate_file = DeletingFileField(
        max_length=255,
        upload_to=get_overstate_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.SALT_STATE_ROOT))

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
            self.props_file.save(self.slug+'.props', ContentFile(props_json))
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
            roles = [c.component.sls_path for c in host.formula_components.all()]
            instance_size = host.instance_size.title
            security_groups = set([
                sg.name for sg in host.security_groups.all()
            ])
            volumes = host.volumes.all()

            fqdn = '{0}.{1}'.format(host.hostname, 
                                    cloud_provider_yaml['append_domain'])

            availability_zone = host.availability_zone.title

            # order_groups define which hosts fall into which groups
            # used by the overstate system for orchestrating the provisioning
            # of the hosts
            order_groups = list(set([c.order for c in host.formula_components.all()]))

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

                        # Grains are very useful when you need to set some 
                        # static information about a machine (e.g., what stack 
                        # id its registered under or how many total machines
                        # are in the cluster)
                        'grains': {
                            'roles': roles,
                            'order_groups': order_groups,
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
                    'securitygroup': list(security_groups),
                    'availability_zone': availability_zone,
                    'volumes': map_volumes,
                }
            }

            # Add in spot instance config if needed
            if host.sir_price:
                host_metadata[host.hostname]['spot_config'] = {
                    'spot_price': str(host.sir_price) # convert to string
                }

            profiles.setdefault(host.cloud_profile.slug, []).append(host_metadata)

        map_file_yaml = yaml.safe_dump(profiles,
                                       default_flow_style=False)

        if not self.map_file:
            self.map_file.save(self.slug+'.map', ContentFile(map_file_yaml))
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
            self.top_file.save('stack_{0}_top.sls'.format(self.pk), ContentFile(top_file_yaml))
        else:
            with open(self.top_file.path, 'w') as f:
                f.write(top_file_yaml)

    def _generate_overstate_file(self): 
        from blueprints.models import BlueprintHostFormulaComponent
        # find the distinct set of formula components for this stack
        components = set()
        hosts = self.hosts.all()
        for host in hosts:
            components.update(list(host.formula_components.all()))
        logger.debug('COMPONENTS: {0}'.format(components))

        i = 0
        overstate = {}
        while True:
            components = BlueprintHostFormulaComponent.objects.filter(
                order=i,
                hosts__in=hosts
            )
            if not components.count():
                break
            group = 'group_{0}'.format(i)
            overstate[group] = {
                'match': 'G@stack_id:{0} and G@order_groups:{1}'.format(self.pk, i),
                'sls': list(set([c.component.sls_path for c in components])),
            }

            if i > 0:
                overstate[group]['require'] = ['group_{0}'.format(i-1)]
            i += 1

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
        formulas = set([c.component.formula for c in BlueprintHostFormulaComponent.objects.filter(
            hosts__in=hosts
        )])
        
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
            logger.info('get_hosts_info: {0!r}'.format(self))
             
            # salt-cloud command to pull host information with
            # a yaml output
            query_cmd = ' '.join([
                'salt-cloud',
                '-m {0}',                   # map file to use
                '-F',                       # execute a full query
                '--out yaml',               # output in yaml format
                # Until environment variables work
                '--providers-config={1}',
                '--profiles={2}',
                '--cloud-config={3}',
            ]).format(
                self.map_file.path,
                settings.SALT_CLOUD_PROVIDERS_DIR,
                settings.SALT_CLOUD_PROFILES_DIR,
                settings.SALT_CLOUD_CONFIG,
            )

            logger.debug('Query hosts command: {0}'.format(query_cmd))
            result = envoy.run(query_cmd)

            # Run the envoy stdout through the yaml parser. The format
            # will always be a dictionary with one key (the provider type)
            # and a value that's a dictionary containing keys for every
            # host in the stack. 
            yaml_result = yaml.safe_load(result.std_out)

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

            logger.debug('query_hosts transform: {0!r}'.format(host_result))
            return host_result

        except Exception, e:
            logger.exception('Unhandled exception')
            raise

    def get_root_directory(self):
        return os.path.dirname(self.map_file.path)

    def get_log_directory(self):
        log_dir = os.path.join(os.path.dirname(self.map_file.path), 'logs')
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        return log_dir

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
    level = models.CharField(max_length=16,
                             choices=(
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
                                      related_name='hosts')

    formula_components = models.ManyToManyField('blueprints.BlueprintHostFormulaComponent',
                                                related_name='hosts')

    hostname = models.CharField(max_length=64)

    security_groups = models.ManyToManyField('cloud.SecurityGroup',
                                             related_name='hosts')
    
    # The machine state as provided by the cloud provider
    state = models.CharField(max_length=32, default='unknown')

    # This must be updated automatically after the host is online.
    # After salt-cloud has launched VMs, we will need to look up
    # the DNS name set by whatever cloud provider is being used
    # and set it here
    provider_dns = models.CharField(max_length=64, blank=True)

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

