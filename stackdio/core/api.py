from django.contrib.auth.models import User

from rest_framework import generics

from .serializers import UserSerializer

class UserListAPIView(generics.ListAPIView):

    model = User
    serializer_class = UserSerializer

class UserDetailAPIView(generics.RetrieveAPIView):

    model = User
    serializer_class = UserSerializer
