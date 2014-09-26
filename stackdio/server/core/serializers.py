from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import UserSettings


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('url',
                  'username',
                  'first_name',
                  'last_name',
                  'email',
                  'last_login')


class UserSettingsSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserSettings
        fields = ('user', 'public_key',)
