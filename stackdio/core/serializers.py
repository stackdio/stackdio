from django.conf import settings

from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = settings.AUTH_USER_MODEL
        fields = ('url', 
                  'username', 
                  'first_name', 
                  'last_name', 
                  'email', 
                  'last_login')
