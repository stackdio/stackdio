import logging

from rest_framework import serializers

from . import models

logger = logging.getLogger(__name__)


class StackPropertiesSerializer(serializers.Serializer):
    def to_native(self, obj):
        if obj is not None:
            return obj.properties
        return {}


class HostSerializer(serializers.HyperlinkedModelSerializer):
    availability_zone = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = models.Host
        fields = (
            'id',
            'url',
            'hostname', 
            'provider_dns', 
            'fqdn', 
            'state',
            'status',
            'status_detail',
            'availability_zone',
            'created',
            'sir_id',
            'sir_price'
        )


class StackHistorySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.StackHistory
        fields = (
            'event',
            'status',
            'level',
            'created'
        )


class StackSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.Field()
    hosts = serializers.HyperlinkedIdentityField(view_name='stack-hosts')
    host_count = serializers.Field(source='hosts.count')
    volumes = serializers.HyperlinkedIdentityField(view_name='stack-volumes')
    volume_count = serializers.Field(source='volumes.count')
    history = StackHistorySerializer(many=True)
    properties = serializers.HyperlinkedIdentityField(view_name='stack-properties')

    class Meta:
        model = models.Stack
        fields = (
            'title', 
            'description',
            'id',
            'url',
            'owner',
            'blueprint',
            'hosts',
            'host_count',
            'volumes',
            'volume_count',
            'properties',
            'created', 
            'history',
        )

