from django.conf import settings
from django.db import models
from django.core.files.storage import FileSystemStorage

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from core.fields import DeletingFileField

def get_map_file_path(obj, filename):
    return "stacks/{0}/{1}.map".format(obj.user.username, obj.slug)

class Stack(TimeStampedModel, TitleSlugDescriptionModel):


    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='stacks')

    map_file = DeletingFileField(
        max_length=255, 
        upload_to=get_map_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    def __unicode__(self):
        return self.title


class Role(TimeStampedModel, TitleSlugDescriptionModel):


    role_name = models.CharField(max_length=64)
    
    
class StackMetdata(TimeStampedModel, TitleSlugDescriptionModel):


    stack = models.ForeignKey(Stack, related_name='metadata')
    role = models.ForeignKey(Role)
    instance_count = models.IntegerField(default=0)
    host_pattern = models.CharField(max_length=32)


class Host(TimeStampedModel, TitleSlugDescriptionModel):


    stack = models.ForeignKey(Stack, related_name='hosts')
    role = models.ForeignKey(Role, related_name='hosts')


