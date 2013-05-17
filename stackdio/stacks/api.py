from rest_framework import generics
from rest_framework import parsers

from core.exceptions import ResourceConflict

from .models import Stack, Host, Role
from .serializers import StackSerializer, HostSerializer, RoleSerializer

class StackListAPIView(generics.ListCreateAPIView):

    model = Stack
    serializer_class = StackSerializer
    parser_classes = (parsers.JSONParser,)

    def pre_save(self, obj):
        # check for duplicates
        if Stack.objects.filter(user=self.request.user, title=obj.title).count():
            raise ResourceConflict('A Stack resource already exists with ' \
                                   'the given parameters.')

        obj.user = self.request.user

class StackDetailAPIView(generics.RetrieveDestroyAPIView):

    model = Stack
    serializer_class = StackSerializer


class HostListAPIView(generics.ListAPIView):

    model = Host
    serializer_class = HostSerializer


class RoleListAPIView(generics.ListAPIView):

    model = Role
    serializer_class = RoleSerializer

