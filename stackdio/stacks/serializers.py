from .models import Stack, Host, Role

from rest_framework import serializers

class StackSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.Field()

    class Meta:
        model = Stack
        fields = (
            'url',
            'user',
            'created', 
            'title', 
            'description',
            'map_file',
        )

class HostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Host
        fields = (
            'url',
            'created', 
            'title', 
        )

class RoleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Role
        fields = (
            'url', 
            'created', 
            'title', 
        )
