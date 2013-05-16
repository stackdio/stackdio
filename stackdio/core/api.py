from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import generics

from .serializers import UserSerializer

class UserListAPIView(generics.ListAPIView):

    model = settings.AUTH_USER_MODEL
    serializer_class = UserSerializer

class UserDetailAPIView(generics.RetrieveAPIView):

    model = settings.AUTH_USER_MODEL
    serializer_class = UserSerializer
