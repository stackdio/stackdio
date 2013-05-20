import logging

from rest_framework import generics
from rest_framework import parsers
from rest_framework.response import Response

from core.exceptions import ResourceConflict, BadRequest

from .models import Stack, Host, Role, StackMetadata
from .serializers import StackSerializer, HostSerializer, RoleSerializer

logger = logging.getLogger(__name__)

class StackListAPIView(generics.ListCreateAPIView):

    model = Stack
    serializer_class = StackSerializer
    parser_classes = (parsers.JSONParser,)

    def pre_save(self, obj):
        '''
        Check for duplicates and also make sure Stacks are owned
        by the right user.
        '''

        # check for duplicates
        if Stack.objects.filter(user=self.request.user, title=obj.title).count():
            raise ResourceConflict('A Stack resource already exists with ' \
                                   'the given parameters.')

        obj.user = self.request.user

    def post(self, request, *args, **kwargs):
        '''
        Overriding post to create roles and metadata objects for this Stack
        as well as generating the salt-cloud map that will be used to launch
        machines
        '''

        # create the stack object and foreign key objects
        stack = Stack.objects.create_stack(request.user, request.DATA)

        # TODO: Queue up stack creation using Celery
    
        # return serialized stack object
        serializer = StackSerializer(stack)
        return Response(serializer.data)

class StackDetailAPIView(generics.RetrieveDestroyAPIView):

    model = Stack
    serializer_class = StackSerializer

class HostListAPIView(generics.ListAPIView):

    model = Host
    serializer_class = HostSerializer

class StackHostsAPIView(HostListAPIView):

    def get_queryset(self):
        return Host.objects.filter(stack__pk=self.kwargs.get('pk'))

class HostDetailAPIView(generics.RetrieveAPIView):

    model = Host
    serializer_class = HostSerializer


class RoleListAPIView(generics.ListAPIView):

    model = Role
    serializer_class = RoleSerializer

