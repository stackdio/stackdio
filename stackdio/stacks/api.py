from rest_framework import generics

from .models import Stack, Host, Role
from .serializers import StackSerializer, HostSerializer, RoleSerializer

class StackListAPIView(generics.ListAPIView):

    model = Stack
    serializer_class = StackSerializer


class HostListAPIView(generics.ListAPIView):

    model = Host
    serializer_class = HostSerializer


class RoleListAPIView(generics.ListAPIView):

    model = Role
    serializer_class = RoleSerializer

