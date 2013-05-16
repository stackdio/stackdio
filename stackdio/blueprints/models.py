from django.db import models
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

class Blueprint(TimeStampedModel, TitleSlugDescriptionModel):
    name = models.CharField(max_length=64)