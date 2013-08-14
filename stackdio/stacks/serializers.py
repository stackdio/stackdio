import logging

from rest_framework import serializers

from .models import (
    Stack, 
    Host, 
    SaltRole,
)

logger = logging.getLogger(__name__)

class HostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Host
        fields = (
            'url',
            'hostname', 
            'provider_dns', 
            'fqdn', 
            'state',
            'status',
            'status_detail',
            'created',
            'sir_id',
            'sir_max_price'
        )

class StackSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.Field()
    hosts = serializers.HyperlinkedIdentityField(view_name='stack-hosts')
    host_count = serializers.Field(source='hosts.count')
    volumes = serializers.HyperlinkedIdentityField(view_name='stack-volumes')
    volume_count = serializers.Field(source='volumes.count')
    status = serializers.Field()
    status_detail = serializers.Field()

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
            'status',
            'status_detail',
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
