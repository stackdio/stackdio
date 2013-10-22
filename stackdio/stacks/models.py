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
import simplejson
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

logger = logging.getLogger(__name__)


HOST_INDEX_PATTERN = re.compile('.*-.*-(\d+)')

def get_hosts_file_path(obj, filename):
    return "stacks/{0}/{1}.hosts".format(obj.owner.username, obj.slug)

def get_map_file_path(obj, filename):
    return "stacks/{0}/{1}.map".format(obj.owner.username, obj.slug)

def get_top_file_path(obj, filename):
    return "stack_{0}_top.sls".format(obj.id)

def get_pillar_file_path(obj, filename):
    return "stacks/{0}/{1}.pillar".format(obj.owner.username, obj.slug)


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
                           #cloud_provider=cloud_provider)
        stack.save()

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
            sg_name='{0}-stackdio-id-{1}'.format(hostdef.prefix, stack.pk)
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
                hostname = '{0}-{1}-{2}'.format(hostdef.prefix,
                                                owner.username,
                                                i)
                host = stack.hosts.create(cloud_profile=hostdef.cloud_profile,
                                          instance_size=hostdef.size,
                                          availability_zone=hostdef.zone,
                                          hostname=hostname)

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

                # TODO: Volumes
                # TODO: Spot instances

        # Generate configuration files for salt and salt-cloud
        # NOTE: The order is important here. pillar must be available before
        # the map file is rendered or else we'll miss important grains that
        # need to be set at launch time
        stack._generate_pillar_file()
        stack._generate_top_file()
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

    #XXX
    # The cloud provider this stack will use -- it may use any cloud profile
    # defined for that provider.
    #cloud_provider = models.ForeignKey('cloud.CloudProvider', related_name='stacks')

    #XXX
    # Where on disk a JSON representation of the hosts file is stored
    #hosts_file = DeletingFileField(
    #    max_length=255,
    #    upload_to=get_hosts_file_path,
    #    null=True,
    #    blank=True,
    #    default=None,
    #    storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

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

    # Where on disk is the custom pillar file for custom configuration for
    # all salt states used by the top file
    pillar_file = DeletingFileField(
        max_length=255,
        upload_to=get_pillar_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    # Use our custom manager object
    objects = StackManager()

    def __unicode__(self):
        return u'{0} (id={1})'.format(self.title, self.id)

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
    
    #XXX
    def create_hosts_XXX(self):
        '''
        See StackManager.create_stack for host data format requirements and
        how the Stack.hosts_file is populated. 
        
        Calling create_hosts after hosts are already attached to the Stack
        object will log a warning and return. 
        '''
        # TODO: We probably need to think about adding and deleting
        # individual hosts.

        # if the stack already has hosts, do nothing
        if self.get_hosts().count() > 0:
            logger.warn('Stack already has host objects attached. '
                        'Skipping create_hosts')
            return

        # load the stack's hosts file
        with open(self.hosts_file.path, 'r') as f:
            hosts = simplejson.loads(f.read())

        # load the provider yaml
        provider_yaml = yaml.safe_load(self.cloud_provider.yaml).values()[0]

        new_hosts = []
        for host in hosts:
            host_count = int(host['host_count'])
            host_pattern = host['host_pattern']
            cloud_profile_id = host['cloud_profile']
            host_size_id = host.get('host_size')
            availability_zone_id = host.get('availability_zone')
            security_group_ids = host.get('host_security_groups', [])

            # cloud profiles are restricted to only those in this stack's
            # cloud provider
            cloud_profile_obj = CloudProfile.objects.get(
                id=cloud_profile_id,
                cloud_provider=self.cloud_provider
            )

            # default to the cloud profile instance size
            # if the user is not overriding it
            if host_size_id is None:
                host_size_id = cloud_profile_obj.default_instance_size.id
            host_size_obj = CloudInstanceSize.objects.get(id=host_size_id)

            # default to the cloud profile availability zone if
            # the user is not supplying it
            if availability_zone_id is None:
                availability_zone_id = cloud_profile_obj \
                    .cloud_provider \
                    .default_availability_zone \
                    .id
            availability_zone_obj = CloudZone.objects.get(id=availability_zone_id)

            salt_roles = host['salt_roles']
            # optional
            volumes = host.get('volumes', [])

            # PI-48: Spot instance support
            spot_config = host.get('spot_config', {})
            sir_price = spot_config.get('spot_price')

            # Security groups are a combination of the default groups
            # set on the provider and those in the host definition
            
            # pull the default security groups from the provider
            provider_groups = list(self.cloud_provider.security_groups.filter(
                is_default=True
            ))

            # groups set by the user on the host
            host_groups = list(SecurityGroup.objects.filter(
                owner=self.owner,
                pk__in=security_group_ids
            ))

            security_group_objs = set(provider_groups+host_groups)

            # lookup other objects
            role_objs = SaltRole.objects.filter(id__in=salt_roles)

            # if user is adding hosts, they may be adding hosts that will
            # use the same host pattern as an existing hostname. in that case
            # we need to find which starting index of the hostname pattern to
            # use
            existing_hosts = self.hosts.filter(
                hostname__contains=host_pattern
            )
            matches = [int(HOST_INDEX_PATTERN.match(h.hostname).groups()[0]) 
                for h in existing_hosts]
            start_index = max(matches) if matches else 0

            # create hosts
            for i in xrange(start_index+1, start_index+host_count+1):
                host_obj = self.hosts.create(
                    stack=self,
                    cloud_profile=cloud_profile_obj,
                    instance_size=host_size_obj,
                    availability_zone=availability_zone_obj,
                    hostname='{0}-{1}-{2}'.format(host_pattern, 
                                               self.owner.username, 
                                               i),
                )

                if sir_price is not None:
                    host_obj.sir_price = Decimal(sir_price)
                    host_obj.save()

                # set security groups
                host_obj.security_groups.add(*security_group_objs)

                # set roles
                host_obj.roles.add(*role_objs)

                cloud_provider = host_obj.cloud_profile.cloud_provider

                # add volumes - first, we need to check the stack to see
                # if existing volumes are available
                existing_volumes = self.volumes.filter(hostname=host_obj.hostname)

                # in this case, the volumes have already been created,
                # so we need to match up the volumes with the host
                # objects based on the hostname
                if existing_volumes:
                    existing_volumes.update(host=host_obj)

                # this case means we're dealing with a stack that hasn't
                # had volumes before, so we create them in the database.
                # The volume_id for the new volumes will be assigned
                # after hosts have been launched and the volumes created
                # and attached to the hosts
                else:
                    for volume in volumes:
                        self.volumes.create(
                            hostname=host_obj.hostname,
                            host=host_obj,
                            snapshot=cloud_provider.snapshots.get(id=volume['snapshot']),
                            device=volume['device'],
                            mount_point=volume['mount_point'])

                # keep track of the hosts we're creating so we can return them
                new_hosts.append(host_obj)

        # generate salt and salt-cloud files
        # NOTE: The order is important here. pillar must be available before
        # the map file is rendered or else we'll miss important grains that
        # need to be set
        self._generate_pillar_file()
        self._generate_top_file()
        self._generate_map_file()

        # return the newly added host objects
        return new_hosts

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
            roles = [c.sls_path for c in host.formula_components.all()]
            instance_size = host.instance_size.title
            security_groups = set([
                sg.name for sg in host.security_groups.all()
            ])
            volumes = host.volumes.all()

            fqdn = '{0}.{1}'.format(host.hostname, 
                                    cloud_provider_yaml['append_domain'])

            availability_zone = host.availability_zone.title

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
                            'stack_id': int(self.id),
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
        top_file_data = {}

        # Core SLS
        stack_match = 'G@stack_id:{0}'.format(self.id)
        top_file_data[stack_match] = [
            {'match': 'compound'},
            'core.*',
        ]

        # find the distinct set of formula components for this stack
        components = set()
        for host in self.hosts.all():
            components.update(list(host.formula_components.all()))

        # build up the top file using compound matching based
        # on the stack id and components
        for component in components:
            matcher = stack_match + ' and G@roles:{0}'.format(component.sls_path)
            top_file_data[matcher] = [
                {'match': 'compound'},
                component.sls_path
            ]

        top_file_data = {
            'base': top_file_data
        }
        top_file_yaml = yaml.safe_dump(top_file_data, default_flow_style=False)

        if not self.top_file:
            self.top_file.save('stack_{0}_top.sls'.format(self.id), ContentFile(top_file_yaml))
        else:
            with open(self.top_file.path, 'w') as f:
                f.write(top_file_yaml)

    def _generate_pillar_file(self):
        pillar_file_yaml = yaml.safe_dump({
            'stackdio_username': self.owner.username,
            'stackdio_publickey': self.owner.settings.public_key,
        }, default_flow_style=False)

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
                '--out yaml'                # output in yaml format
            ]).format(self.map_file.path)

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


class SaltRole(TimeStampedModel, TitleSlugDescriptionModel):
    sls_path = models.CharField(max_length=64)

    def __unicode__(self):
        return self.title


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

    formula_components = models.ManyToManyField('formulas.FormulaComponent',
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
