from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import (
    generics,
    permissions,
)

from .serializers import (
    UserSerializer,
    UserSettingsSerializer,
)

from .models import (
    UserSettings,
)


class UserListAPIView(generics.ListAPIView):

    model = get_user_model()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)


class UserDetailAPIView(generics.RetrieveAPIView):

    model = get_user_model()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)


class UserSettingsDetailAPIView(generics.RetrieveUpdateAPIView):

    model = UserSettings
    serializer_class = UserSettingsSerializer

    def get_object(self):
        return self.request.user.settings
