import logging

from rest_framework import serializers

from .models import Stack, Host, Role

logger = logging.getLogger(__name__)

class HostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Host
        fields = (
            'url',
            'hostname', 
            'created', 
        )

class StackSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.Field()
    hosts = serializers.HyperlinkedIdentityField(view_name='stack-hosts')

    class Meta:
        model = Stack
        fields = (
            'url',
            'user',
            'hosts',
            'created', 
            'title', 
            'description',
            'status',
            'status_detail',
        )

class RoleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Role
        fields = (
            'url', 
            'created', 
            'title', 
        )
