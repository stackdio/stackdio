import logging

from rest_framework import serializers

from .models import (
    Stack, 
    StackHistory,
    Host, 
    SaltRole,
)

logger = logging.getLogger(__name__)

class HostSerializer(serializers.HyperlinkedModelSerializer):
    availability_zone = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = Host
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
        model = StackHistory
        fields = (
            'event',
            'status',
            'level',
            'created'
        )


class StackSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.Field()
    hosts = serializers.HyperlinkedIdentityField(view_name='stack-hosts')
    host_count = serializers.Field(source='hosts.count')
    volumes = serializers.HyperlinkedIdentityField(view_name='stack-volumes')
    volume_count = serializers.Field(source='volumes.count')
    history = StackHistorySerializer(many=True)

    class Meta:
        model = Stack
        fields = (
            'id',
            'url',
            'user',
            'cloud_provider',
            'hosts',
            'host_count',
            'volumes',
            'volume_count',
            'created', 
            'title', 
            'slug',
            'description',
            'history',
        )


class SaltRoleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SaltRole
        fields = (
            'id', 
            'url', 
            'created', 
            'title', 
            'role_name', 
        )
