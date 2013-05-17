from django.conf import settings
from django.db import models
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

class Stack(TimeStampedModel, TitleSlugDescriptionModel):


    user = models.ForeignKey(settings.AUTH_USER_MODEL, 
                             null=True, 
                             blank=True, 
                             related_name='stacks')


class Role(TimeStampedModel, TitleSlugDescriptionModel):


    role_name = models.CharField(max_length=64)
    
    
class StackMetdata(TimeStampedModel, TitleSlugDescriptionModel):


    stack = models.ForeignKey(Stack, null=True, blank=True, related_name='metadata')
    role = models.ForeignKey(Role, null=True, blank=True)
    instance_count = models.IntegerField(default=0)
    host_pattern = models.CharField(max_length=32)


class Host(TimeStampedModel, TitleSlugDescriptionModel):


    stack = models.ForeignKey(Stack, null=True, blank=True, related_name='hosts')
    role = models.ForeignKey(Role, null=True, blank=True, related_name='hosts')


