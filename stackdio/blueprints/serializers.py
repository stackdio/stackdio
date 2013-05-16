from django.conf import settings

from rest_framework import serializers

class BlueprintSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = settings.AUTH_USER_MODEL
        fields = ('created', 
                  'modified', 
                  'title', 
                  'name', 
                  'slug', 
                  'description', 
                  )
