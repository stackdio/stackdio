from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import (
    generics,
    permissions,
)

from .serializers import (
    UserSerializer,
)


class UserListAPIView(generics.ListAPIView):

    model = get_user_model()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)


class UserDetailAPIView(generics.RetrieveAPIView):

    model = get_user_model()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)

