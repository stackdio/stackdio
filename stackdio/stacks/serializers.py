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
            'public_dns', 
            'created', 
        )

class StackSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.Field()
    hosts = serializers.HyperlinkedIdentityField(view_name='stack-hosts')

    class Meta:
        model = Stack
        fields = (
            'id',
            'url',
            'user',
            'hosts',
            'created', 
            'title', 
            'description',
            'status',
            'status_detail',
        )

    def validate(self, attrs):

        # validate provider specific request data
        request = self.context['request']

        errors = {
            'foo': ['Missing some stuff'],
        }
        raise serializers.ValidationError(errors)

        return attrs    

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
