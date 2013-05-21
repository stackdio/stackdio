from django.db import models

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

class CloudProviderType(models.Model):


    # TODO: Probably should detect what providers are available, but how?
    PROVIDER_TYPES = (('AWS', 'aws'),)

    type_name = models.CharField(max_length=32, choices=PROVIDER_TYPES)

class CloudProvider(TimeStampedModel, TitleSlugDescriptionModel):


    cloud_provider_type = models.ForeignKey('CloudProviderType')

class CloudProviderInstanceSize(TitleSlugDescriptionModel):
    pass
