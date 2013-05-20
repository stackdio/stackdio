import logging
from socket import getfqdn

from django.conf import settings
from django.db import models, transaction
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

import yaml
import model_utils.models

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel
from model_utils import Choices

from core.fields import DeletingFileField

logger = logging.getLogger(__name__)

def get_map_file_path(obj, filename):
    return "stacks/{0}/{1}.map".format(obj.user.username, obj.slug)

class StatusModel(model_utils.models.StatusModel):
    status_detail = models.TextField(blank=True)

    class Meta:
        abstract = True

class StackManager(models.Manager):
    
    @transaction.commit_on_success
    def create_stack(self, user, data):
        '''
        data is a JSON object that looks something like:

        {
            "title": "Abe's CDH4 Cluster",
            "description": "Abe's personal cluster for testing CDH4 and stuff...",
            "roles": [
                {
                    "id": 1,
                    "instance_count": 1,
                    "host_pattern": "abe-nn"
                },
                {
                    "id": 2,
                    "instance_count": 10,
                    "host_pattern": "abe-dn"
                }
            ]
        }
        '''

        stack_obj = self.model(title=data['title'],
                               description=data['description'],
                               user=user)
        stack_obj.save()

        for role in data['roles']:
            instance_count = role['instance_count']
            host_pattern = role['host_pattern']

            # pull role objects
            role_obj = Role.objects.get(id=role['id'])

            # create metadata
            metadata = stack_obj.metadata.create(
                stack=stack_obj,
                role=role_obj,
                instance_count=instance_count,
                host_pattern=host_pattern
            )

            # create hosts
            for i in xrange(1, instance_count+1):
                host = stack_obj.hosts.create(
                    stack=stack_obj, 
                    role=role_obj,
                    hostname='%s-%d' % (host_pattern, i),
                )

        # generate stack
        stack_obj._generate_map_file()

        return stack_obj

class Stack(TimeStampedModel, TitleSlugDescriptionModel, StatusModel):
    STATUS = Choices('pending', 'launching', 'provisioning', 'finished', 'error')

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

    objects = StackManager()

    def __unicode__(self):
        return self.title

    def _generate_map_file(self):

        # TODO: Should we store this somewhere instead of assuming
        # the master will always be this box?
        master = getfqdn()

        map_file_dict = {}
        provider_dict = {}

        for host in self.hosts.all():
            roles = [
                host.role.role_name 
            ]
            provider_dict[host.hostname] = {
                'minion': {
                    'master': master,
                    'grains': {
                        'roles': roles
                    }
                },
            }
        map_file_dict['provider_goes_here'] = provider_dict
        map_file_yaml = yaml.safe_dump(map_file_dict, 
                                       default_flow_style=False)

        if not self.map_file:
            self.map_file.save(self.slug+'.map', ContentFile(map_file_yaml))
        else:
            with open(self.map_file.file, 'w') as f:
                f.write(map_file_yaml)

class Role(TimeStampedModel, TitleSlugDescriptionModel):


    role_name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.title
    
    
class StackMetadata(TimeStampedModel):


    stack = models.ForeignKey(Stack, related_name='metadata')
    role = models.ForeignKey(Role)
    instance_count = models.IntegerField(default=0)
    host_pattern = models.CharField(max_length=32)

    def __unicode__(self):
        return 'Stack %r, role %r' % (self.stack, self.role)


class Host(TimeStampedModel):


    stack = models.ForeignKey(Stack, related_name='hosts')
    role = models.ForeignKey(Role, related_name='hosts')
    hostname = models.CharField(max_length=64)

    def __unicode__(self):
        return 'Stack %r, role %r' % (self.stack, self.role)

