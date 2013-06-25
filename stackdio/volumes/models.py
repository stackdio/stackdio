import logging

from django.conf import settings
from django.db import models
from django.core.files.storage import FileSystemStorage

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

class Volume(TimeStampedModel, TitleSlugDescriptionModel):

    def __unicode__(self):
        return self.title