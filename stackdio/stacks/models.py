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


def get_map_file_path(obj, filename):
    return "stacks/{0}/{1}.map".format(obj.user.username, obj.slug)


def get_top_file_path(obj, filename):
    return "stack_{}_top.sls".format(obj.id)


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

        for host in data['hosts']:
            host_count = host['host_count']
            host_size = host['host_size']
            host_pattern = host['host_pattern']
            cloud_profile = host['cloud_profile']
            salt_roles = host['salt_roles']

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

            # create hosts
            for i in xrange(1, host_count+1):
                host_obj = stack_obj.hosts.create(
                    stack=stack_obj,
                    cloud_profile=cloud_profile_obj,
                    instance_size=host_size_obj,
                    hostname='%s-%d' % (host_pattern, i),
                )

                # set security groups
                host_obj.security_groups.add(*security_group_objs)

                # set roles
                host_obj.roles.add(*role_objs)

        # generate salt and salt-cloud files
        stack_obj._generate_map_file()
        stack_obj._generate_top_file()

        return stack_obj


class Stack(TimeStampedModel, TitleSlugDescriptionModel, StatusDetailModel):
    PENDING = 'pending'
    LAUNCHING = 'launching'
    CONFIGURING = 'configuring'
    PROVISIONING = 'provisioning'
    FINALIZING = 'finalizing'
    FINISHED = 'finished'
    ERROR = 'error'
    DESTROYING = 'destroying'
    STATUS = Choices(PENDING, 
                     LAUNCHING, 
                     PROVISIONING, 
                     FINISHED, 
                     ERROR,
                     DESTROYING)

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

    objects = StackManager()

    def __unicode__(self):
        return self.title

    def _generate_map_file(self):

        # TODO: Should we store this somewhere instead of assuming
        # the master will always be this box?
        master = socket.getfqdn()

        profiles = collections.defaultdict(list)

        for host in self.hosts.all():
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

            # add in cloud provider security groups
            security_groups.add(*cloud_provider_yaml['securitygroup'])

            profiles[host.cloud_profile.slug].append({
                host.hostname: {
                    'size': instance_size,
                    'securitygroup': list(security_groups),
                    'minion': {
                        'master': master,
                        'grains': {
                            'roles': roles,
                            'stack_id': int(self.id),
                        }
                    },
                }
            })
        map_file_yaml = yaml.safe_dump(dict(profiles),
                                       default_flow_style=False)

        if not self.map_file:
            self.map_file.save(self.slug+'.map', ContentFile(map_file_yaml))
        else:
            with open(self.map_file.file, 'w') as f:
                f.write(map_file_yaml)

    def _generate_top_file(self):
        top_file_data = {}

        for host in self.hosts.all():
            top_file_data[host.hostname] = [r.role_name for r in host.roles.all()]

        top_file_data = {
            'base': top_file_data
        }
        top_file_yaml = yaml.safe_dump(top_file_data, default_flow_style=False)

        if not self.top_file:
            self.top_file.save('stack_{}_top.sls'.format(self.id), ContentFile(top_file_yaml))
        else:
            with open(self.top_file.file, 'w') as f:
                f.write(top_file_yaml)

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
            provider_type, result = yaml.safe_load(result.std_out).popitem()
            return result

        except Exception, e:
            logger.exception('Unhandled exception')
            raise

    def create_dns_resource_records(self):
        '''
        '''
        hosts = self.query_hosts()

    def delete_dns_resource_records(self):
        '''
        '''
        hosts = self.query_hosts()


class SaltRole(TimeStampedModel, TitleSlugDescriptionModel):
    role_name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.title


class Host(TimeStampedModel):
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

    hostname = models.CharField(max_length=64)

    security_groups = models.ManyToManyField('stacks.SecurityGroup',
                                             related_name='hosts')

    # This must be updated automatically after the host is online.
    # After salt-cloud has launched VMs, we will need to look up
    # the DNS name set by whatever cloud provider is being used
    # and set it here
    public_dns = models.CharField(max_length=64, blank=True)

    def __unicode__(self):
        return self.hostname

    def get_provider(self):
        return self.cloud_profile.cloud_provider

    def get_provider_type(self):
        return self.cloud_profile.cloud_provider.provider_type


class SecurityGroup(TimeStampedModel):
    group_name = models.CharField(max_length=64)
