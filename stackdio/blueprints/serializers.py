from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers

class BlueprintSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('created', 
                  'modified', 
                  'title', 
                  'name', 
                  'slug', 
                  'description', 
                  )
