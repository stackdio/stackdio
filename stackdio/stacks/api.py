import logging
import celery
from collections import defaultdict

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

from .serializers import (
    StackSerializer, 
    HostSerializer, 
    SaltRoleSerializer,
)

logger = logging.getLogger(__name__)


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

        # Queue up stack creation and provisioning using Celery
        task_chain = (
            tasks.launch_stack.si(stack.id) | 
            tasks.configure_dns.si(stack.id) | 
            tasks.provision_stack.si(stack.id) |
            tasks.finish_stack.si(stack.id)
        )
        
        # execute the chain
        task_chain()

        # return serialized stack object
        serializer = StackSerializer(stack, context={
            'request': request,
        })
        return Response(serializer.data)


class StackDetailAPIView(generics.RetrieveDestroyAPIView):
    model = Stack
    serializer_class = StackSerializer

    def delete(self, request, *args, **kwargs):
        '''
        Overriding the delete method to make sure the stack
        is taken offline before being deleted
        '''
        # Update the status
        stack = self.get_object()
        msg = 'Stack will be removed upon successful termination ' \
              'of all machines'
        stack.set_status(Stack.DESTROYING, msg)
        logger.debug(stack)
        logger.debug(stack.status_detail)

        # Async destroy the stack
        tasks.destroy_stack.delay(stack.id)

        # Return the stack while its deleting
        serializer = self.get_serializer(stack)
        return Response(serializer.data)

class HostListAPIView(generics.ListAPIView):
    model = Host
    serializer_class = HostSerializer


class StackHostsAPIView(HostListAPIView):
    def get_queryset(self):
        return Host.objects.filter(stack__pk=self.kwargs.get('pk'))

    def get(self, request, *args, **kwargs):
        '''
        Override get method to add additional host-specific info
        to the result that is looked up via salt.
        '''
        result = super(StackHostsAPIView, self).get(request, *args, **kwargs)

        stack = request.user.stacks.get(id=kwargs.get('pk'))
        query_results = stack.query_hosts()

        # TODO: query_results are highly dependent on the underlying
        # salt-cloud driver and there's no guarantee that the result
        # format for AWS will be the same for Rackspace. In the future,
        # we should probably pass the results off to the cloud provider
        # implementation to format into a generic result for the user
        for host in result.data['results']:
            hostname = host['hostname']
            host.update(query_results[hostname]['extra'])

        return result

class HostDetailAPIView(generics.RetrieveAPIView):
    model = Host
    serializer_class = HostSerializer


class SaltRoleListAPIView(generics.ListAPIView):
    model = SaltRole
    serializer_class = SaltRoleSerializer

