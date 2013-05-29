from django import forms
from django.conf import settings
from rest_framework import serializers

from .models import (
    CloudProvider, 
    CloudProviderType,
    CloudInstanceSize,
    CloudProfile,
)

from .utils import get_provider_type_and_class

class CloudProviderSerializer(serializers.HyperlinkedModelSerializer):
    yaml = serializers.Field()

    provider_type = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = CloudProvider
        fields = (
            'url',
            'title', 
            'slug', 
            'description', 
            'provider_type',
            'yaml',
        )

    def validate(self, attrs):

        # validate provider specific request data
        request = self.context['request']

        provider_type, provider_class = \
            get_provider_type_and_class(request.DATA.get('provider_type'))

        provider = provider_class()
        result, errors = provider.validate_provider_data(request.DATA, 
                                                         request.FILES)
        
        if not result:
            raise serializers.ValidationError(errors)

        return attrs

class CloudProviderTypeSerializer(serializers.HyperlinkedModelSerializer):
    title = serializers.Field(source='get_type_name_display')

    class Meta:
        model = CloudProviderType
        fields = (
            'url',
            'title', 
            'type_name', 
        )

class CloudInstanceSizeSerializer(serializers.HyperlinkedModelSerializer):
    provider_type = serializers.Field(source='provider_type')

    class Meta:
        model = CloudInstanceSize
        fields = (
            'url',
            'title', 
            'slug', 
            'description', 
            'provider_type', 
            'instance_id', 
        )

class CloudProfileSerializer(serializers.HyperlinkedModelSerializer):
    cloud_provider = serializers.PrimaryKeyRelatedField()
    default_instance_size = serializers.PrimaryKeyRelatedField()
    class Meta:
        model = CloudProfile
        fields = (
            'url',
            'title', 
            'slug',
            'description',
            'cloud_provider',
            'image_id',
            'default_instance_size',
            'script',
            'ssh_user',
        )
