from django.conf import settings
from rest_framework import serializers

from .models import CloudProvider

class CloudProviderSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CloudProvider
        fields = (
                  'title', 
                  'slug', 
                  'description', 
                  )
