from django import forms
from django.conf import settings
from rest_framework import serializers

from .models import (
    CloudProvider, 
    CloudProviderType,
    CloudInstanceSize,
    CloudProfile,
)

class CloudProviderSerializer(serializers.HyperlinkedModelSerializer):
    private_key_file = serializers.FileField(max_length=255,
                                             allow_empty_file=False)
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
            'private_key_file',
            'yaml',
        )

class CloudProviderTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CloudProviderType
        fields = (
            'url',
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
