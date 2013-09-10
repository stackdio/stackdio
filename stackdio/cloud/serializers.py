import logging
from django import forms
from django.conf import settings
from rest_framework import serializers

from core.mixins import SuperuserFieldsMixin

from .models import (
    CloudProvider, 
    CloudProviderType,
    CloudInstanceSize,
    CloudProfile,
    Snapshot,
    CloudZone,
)

from .utils import get_provider_type_and_class

logger = logging.getLogger(__name__)

class CloudProviderSerializer(SuperuserFieldsMixin,
                              serializers.HyperlinkedModelSerializer):
    yaml = serializers.Field()
    provider_type = serializers.PrimaryKeyRelatedField()
    default_availability_zone = serializers.PrimaryKeyRelatedField()
    provider_type_name = serializers.Field(source='provider_type.type_name')

    class Meta:
        model = CloudProvider
        fields = (
            'id',
            'url',
            'title', 
            'slug', 
            'description', 
            'provider_type',
            'provider_type_name',
            'default_availability_zone',
            'yaml',
        )

        superuser_fields = ('yaml',)

    def validate(self, attrs):

        # validate provider specific request data
        request = self.context['request']

        provider_type, provider_class = get_provider_type_and_class(request.DATA.get('provider_type'))

        provider = provider_class()
        result, errors = provider.validate_provider_data(request.DATA, 
                                                         request.FILES)
        
        if not result:
            logger.error('Cloud provider validation errors: '
                         '{0}'.format(errors))
            raise serializers.ValidationError(errors)

        return attrs

class CloudProviderTypeSerializer(serializers.HyperlinkedModelSerializer):
    title = serializers.Field(source='get_type_name_display')

    class Meta:
        model = CloudProviderType
        fields = (
            'id',
            'url',
            'title', 
            'type_name', 
        )

class CloudInstanceSizeSerializer(serializers.HyperlinkedModelSerializer):
    provider_type = serializers.Field(source='provider_type')

    class Meta:
        model = CloudInstanceSize
        fields = (
            'id',
            'url',
            'title', 
            'slug', 
            'description', 
            'provider_type', 
            'instance_id', 
        )


class CloudProfileSerializer(SuperuserFieldsMixin,
                             serializers.HyperlinkedModelSerializer):
    cloud_provider = serializers.PrimaryKeyRelatedField()
    default_instance_size = serializers.PrimaryKeyRelatedField()
    class Meta:
        model = CloudProfile
        fields = (
            'id',
            'url',
            'title', 
            'slug',
            'description',
            'cloud_provider',
            'image_id',
            'default_instance_size',
            'ssh_user',
        )

        superuser_fields = ('image_id',)


class SnapshotSerializer(serializers.HyperlinkedModelSerializer):
    cloud_provider = serializers.PrimaryKeyRelatedField()
    default_instance_size = serializers.PrimaryKeyRelatedField()
    class Meta:
        model = Snapshot
        fields = (
            'id',
            'url',
            'title', 
            'slug',
            'description',
            'cloud_provider',
            'snapshot_id',
            'size_in_gb',
        )


class CloudZoneSerializer(serializers.HyperlinkedModelSerializer):
    provider_type = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = CloudZone
        fields = (
            'id',
            'title',
            'provider_type',
        )
