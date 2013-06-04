import logging

from rest_framework import (
    generics,
    parsers,
    serializers,
)
from rest_framework.response import Response

from core.exceptions import ResourceConflict

from . import tasks
from .models import (
    Stack,
    Host,
    SaltRole,
)

from .serializers import StackSerializer, HostSerializer, SaltRoleSerializer

LOGGER = logging.getLogger(__name__)


class StackListAPIView(generics.ListCreateAPIView):
    '''
    TODO: Add docstring
    '''
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
            raise ResourceConflict('A Stack resource already exists with '
                                   'the given parameters.')

        obj.user = self.request.user

    def post(self, request, *args, **kwargs):
        '''
        Overriding post to create roles and metadata objects for this Stack
        as well as generating the salt-cloud map that will be used to launch
        machines
        '''
        # XXX: remove me when in production
        Stack.objects.all().delete()

        # create the stack object and foreign key objects
        stack = Stack.objects.create_stack(request.user, request.DATA)

        # TODO: Queue up stack creation using Celery
        tasks.launch_stack.delay(stack.id)

        # return serialized stack object
        serializer = StackSerializer(stack, context={
            'request': request,
        })
        return Response(serializer.data)


class StackDetailAPIView(generics.RetrieveDestroyAPIView):
    model = Stack
    serializer_class = StackSerializer


class StackActionAPIView(generics.SingleObjectAPIView):
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


class SaltRoleListAPIView(generics.ListAPIView):
    model = SaltRole
    serializer_class = SaltRoleSerializer
