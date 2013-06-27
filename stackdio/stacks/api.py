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

    def post(self, request, *args, **kwargs):
        '''
        Overriding post to create roles and metadata objects for this Stack
        as well as generating the salt-cloud map that will be used to launch
        machines
        '''
        # set some defaults
        launch_stack = request.DATA.setdefault('launch', True)

        # check for duplicates
        title = request.DATA.get('title')
        if Stack.objects.filter(user=self.request.user, title=title).count():
            raise ResourceConflict('A Stack already exists with the given '
                                   'title.')

        # create the stack object and foreign key objects
        stack = Stack.objects.create_stack(request.user, request.DATA)

        # Queue up stack creation and provisioning using Celery
        task_chain = (
            tasks.launch_hosts.si(stack.id) | 
            tasks.update_metadata.si(stack.id) | 
            tasks.register_dns.si(stack.id) | 
            tasks.provision_hosts.si(stack.id) |
            tasks.finish_stack.si(stack.id)
        )
        
        # execute the chain
        if launch_stack:
            task_chain()

        # return serialized stack object
        serializer = StackSerializer(stack, context={
            'request': request,
        })
        return Response(serializer.data)


class StackDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    model = Stack
    serializer_class = StackSerializer
    parser_classes = (parsers.JSONParser,)

    def put(self, request, *args, **kwargs):
        '''
        Overriding PUT for a stack to be able to add additional
        hosts after a stack has already been created.
        '''
        
        stack = self.get_object()
        new_hosts = stack.add_hosts(request.DATA['hosts'])
        host_ids = [h.id for h in new_hosts]

        # Queue up stack creation and provisioning using Celery
        task_chain = (
            tasks.launch_hosts.si(stack.id, host_ids=host_ids) | 
            tasks.update_metadata.si(stack.id, host_ids=host_ids) | 
            tasks.register_dns.si(stack.id, host_ids=host_ids) | 
            tasks.provision_hosts.si(stack.id, host_ids=host_ids) |
            tasks.finish_stack.si(stack.id, host_ids=host_ids)
        )
        
        # execute the chain
        task_chain()

        serializer = self.get_serializer(stack)
        return Response(serializer.data)

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

        # Queue up stack destroy tasks
        task_chain = (
            tasks.register_volume_delete.si(stack.id) |
            tasks.unregister_dns.si(stack.id) | 
            tasks.destroy_hosts.si(stack.id)
        )
        
        # execute the chain
        task_chain()

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
            host['ec2_metadata'] = query_results[hostname]

        return result

class HostDetailAPIView(generics.RetrieveDestroyAPIView):
    model = Host
    serializer_class = HostSerializer

    def delete(self, request, *args, **kwargs):
        '''
        Override the delete method to first terminate the host
        before destroying the object.
        '''
        # get the stack id for the host
        host = self.get_object()
        volume_ids = [v.id for v in host.volumes.all()]

        host.set_status(Host.DELETING, 'Deleting host.')

        # unregister DNS and destroy the host
        task_chain = (
            tasks.register_volume_delete.si(host.stack.id, host_ids=[host.id]) |
            tasks.unregister_dns.si(host.stack.id, host_ids=[host.id]) | 
            tasks.destroy_hosts.si(host.stack.id, host_ids=[host.id])
        )
        
        # execute the chain
        task_chain()

        # Return the host while its deleting
        serializer = self.get_serializer(host)
        return Response(serializer.data)


class SaltRoleListAPIView(generics.ListAPIView):
    model = SaltRole
    serializer_class = SaltRoleSerializer


class SaltRoleDetailAPIView(generics.RetrieveAPIView):
    model = SaltRole
    serializer_class = SaltRoleSerializer

