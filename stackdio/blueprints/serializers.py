from django.contrib.auth.models import User

from rest_framework import serializers

class BlueprintSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('created', 
                  'modified', 
                  'title', 
                  'slug', 
                  'description', 
                  )
