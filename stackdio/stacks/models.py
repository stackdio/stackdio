import os
import re
import logging
import collections
import socket
import envoy

from django.conf import settings
from django.db import models, transaction
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

import yaml
import model_utils.models

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel
from model_utils import Choices

from core.fields import DeletingFileField
from cloud.models import CloudProfile, CloudInstanceSize

logger = logging.getLogger(__name__)


HOST_INDEX_PATTERN = re.compile('.*-.*-(\d+)')


def get_map_file_path(obj, filename):
    return "stacks/{0}/{1}.map".format(obj.user.username, obj.slug)


def get_top_file_path(obj, filename):
    return "stack_{}_top.sls".format(obj.id)

def get_pillar_file_path(obj, filename):
    return "stacks/{0}/{1}.pillar".format(obj.user.username, obj.slug)


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
    def create_stack(self, user, data):
        '''
        data is a JSON object that looks something like:

        {
            "title": "Abe's CDH4 Cluster",
            "description": "Abe's personal cluster for testing CDH4 and stuff...",
            "hosts": [
                {
                    "host_count": 1,
                    "host_size": 1,         # what instance_size object to use
                    "host_pattern": "foo",  # the naming pattern for the host's
                                            # hostname, in this case the hostname
                                            # would become 'foo-1'
                    "cloud_profile": 1,     # what cloud_profile object to use
                    "salt_roles": [1,2,3],  # what salt_roles to use
                    "host_security_groups": "foo,bar,baz",
                    "volumes": [            # list of volumes to create and 
                                            # attach to the launched hosts
                        {
                            "snapshot": 1,
                            "device": "/dev/sdj"
                        }
                        ...
                    ]
                },
                {
                    ...
                    more hosts
                    ...
                }
            ]
        }
        '''

        stack_obj = self.model(title=data['title'],
                               description=data.get('description'),
                               user=user)
        stack_obj.save()

        if data['hosts']:
            stack_obj.add_hosts(data['hosts'])

        return stack_obj


class Stack(TimeStampedModel, TitleSlugDescriptionModel, StatusDetailModel):
    OK = 'ok'
    ERROR = 'error'
    PENDING = 'pending'
    FINISHED = 'finished'
    LAUNCHING = 'launching'
    FINALIZING = 'finalizing'
    DESTROYING = 'destroying'
    CONFIGURING = 'configuring'
    PROVISIONING = 'provisioning'
    STATUS = Choices(OK,
                     ERROR,
                     PENDING, 
                     FINISHED, 
                     LAUNCHING, 
                     FINALIZING, 
                     DESTROYING,
                     CONFIGURING,
                     PROVISIONING)

    class Meta:

        unique_together = ('user', 'title')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='stacks')

    map_file = DeletingFileField(
        max_length=255,
        upload_to=get_map_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    top_file = DeletingFileField(
        max_length=255,
        upload_to=get_top_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.SALT_STATE_ROOT))

    pillar_file = DeletingFileField(
        max_length=255,
        upload_to=get_pillar_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    objects = StackManager()

    def __unicode__(self):
        return self.title

    def get_provider_hosts_map(self):
        '''
        returns a dictionary where the keys are provider objects and values
        are a list of host objects in that provider.
        '''
        providers = collections.defaultdict(list)
        for host in self.hosts.all():
            providers[host.cloud_profile.cloud_provider].append(host)
        return providers

    def get_hosts(self, host_ids=None):
        if not host_ids:
            return self.hosts.all()
        return self.hosts.filter(id__in=host_ids)
    
    def add_hosts(self, hosts=[]):
        '''
        See StackManager.create_stack for host data format requirements.
        '''

        new_hosts = []
        for host in hosts:
            host_count = host['host_count']
            host_size = host['host_size']
            host_pattern = host['host_pattern']
            cloud_profile = host['cloud_profile']
            salt_roles = host['salt_roles']
            # optional
            volumes = host.get('volumes', [])

            # Get the security group objects
            security_group_objs = [
                SecurityGroup.objects.get_or_create(group_name=g)[0] for
                g in filter(
                    None,
                    set(h.strip() for
                        h in host['host_security_groups'].split(','))
                )]

            # lookup other objects
            role_objs = SaltRole.objects.filter(id__in=salt_roles)
            cloud_profile_obj = CloudProfile.objects.get(id=cloud_profile)
            host_size_obj = CloudInstanceSize.objects.get(id=host_size)

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
                    hostname='{}-{}-{}'.format(host_pattern, 
                                               self.user.username, 
                                               i)
                )

                # set security groups
                host_obj.security_groups.add(*security_group_objs)

                # set roles
                host_obj.roles.add(*role_objs)

                # add volumes
                cloud_provider = host_obj.cloud_profile.cloud_provider
                for volume in volumes:
                    host_obj.volumes.create(
                        user=self.user,
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

        # TODO: Should we store this somewhere instead of assuming
        # the master will always be this box?
        master = socket.getfqdn()

        profiles = collections.defaultdict(list)

        hosts = self.hosts.all()
        cluster_size = len(hosts)

        for host in hosts:
            # load provider yaml to extract default security groups
            cloud_provider = host.cloud_profile.cloud_provider
            cloud_provider_yaml = yaml.safe_load(
                cloud_provider.yaml)[cloud_provider.slug]

            # pull various stuff we need for a host
            roles = [r.role_name for r in host.roles.all()]
            instance_size = host.instance_size.title
            security_groups = set([
                sg.group_name for
                sg in host.security_groups.all()
            ])
            volumes = host.volumes.all()

            # add in cloud provider security groups
            security_groups.add(*cloud_provider_yaml['securitygroup'])

            fqdn = '{0}.{1}'.format(host.hostname, 
                                    cloud_provider_yaml['append_domain'])
            profiles[host.cloud_profile.slug].append({
                host.hostname: {
                    'size': instance_size,
                    'securitygroup': list(security_groups),
                    'minion': {
                        'master': master,
                        'log_level': 'debug',
                        'grains': {
                            'roles': roles,
                            'stack_id': int(self.id),
                            'fqdn': fqdn,
                            'cluster_size': cluster_size,
                            'stack_pillar_file': self.pillar_file.path,
                        }
                    },
                    'volumes': [{
                        'snapshot': v.snapshot.snapshot_id,
                        'device': v.device,
                        'mount_point': v.mount_point,
                    } for v in volumes]
                }
            })

        map_file_yaml = yaml.safe_dump(dict(profiles),
                                       default_flow_style=False)

        if not self.map_file:
            self.map_file.save(self.slug+'.map', ContentFile(map_file_yaml))
        else:
            with open(self.map_file.path, 'w') as f:
                f.write(map_file_yaml)

    def _generate_top_file(self):
        top_file_data = {
            '*': [
                'core.*',
            ]     
        }

        for host in self.hosts.all():
            top_file_data[host.hostname] = [r.role_name for r in host.roles.all()]

        top_file_data = {
            'base': top_file_data
        }
        top_file_yaml = yaml.safe_dump(top_file_data, default_flow_style=False)

        if not self.top_file:
            self.top_file.save('stack_{}_top.sls'.format(self.id), ContentFile(top_file_yaml))
        else:
            with open(self.top_file.path, 'w') as f:
                f.write(top_file_yaml)

    def _generate_pillar_file(self):
        pillar_file_yaml = yaml.safe_dump({
            'custom_var_1': 'one',
            'custom_var_2': 'two',
            'custom_var_3': 'three',
        }, default_flow_style=False)

        if not self.pillar_file:
            self.pillar_file.save('{}.pillar'.format(self.slug), 
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
            yaml_result = yaml.safe_load(result.std_out)

            # Run the envoy stdout through the yaml parser. The format
            # will always be a dictionary with one key (the provider type)
            # and a value that's a dictionary containing keys for every
            # host in the stack. 
            logger.debug('Query hosts result: {0!r}'.format(result.std_out))

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

class SaltRole(TimeStampedModel, TitleSlugDescriptionModel):
    role_name = models.CharField(max_length=64)

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
    roles = models.ManyToManyField('stacks.SaltRole',
                                   related_name='hosts')

    hostname = models.CharField(max_length=255)

    security_groups = models.ManyToManyField('stacks.SecurityGroup',
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

    def __unicode__(self):
        return self.hostname

    def get_provider(self):
        return self.cloud_profile.cloud_provider

    def get_provider_type(self):
        return self.cloud_profile.cloud_provider.provider_type


class SecurityGroup(TimeStampedModel):
    group_name = models.CharField(max_length=64)
