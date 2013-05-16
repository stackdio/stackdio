from .models import Stack, Host, Role

from rest_framework import serializers

class StackSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Stack
        fields = ('created', 
                  'title', 
                  'description', 
                  )

class HostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Host
        fields = ('created', 
                  'title', 
                  )

class RoleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Role
        fields = ('created', 
                  'title', 
                  )
