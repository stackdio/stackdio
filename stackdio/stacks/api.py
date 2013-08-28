import logging
from collections import defaultdict
from operator import or_

import celery
from django.shortcuts import get_object_or_404

from rest_framework import (
    generics,
    parsers,
    serializers,
)
from rest_framework.response import Response

from core.exceptions import (
    ResourceConflict,
    BadRequest,
)

from . import tasks
from .models import (
    Stack,
    StackHistory,
    Host,
    SaltRole,
)

from .serializers import (
    StackSerializer, 
    StackHistorySerializer, 
    HostSerializer, 
    SaltRoleSerializer,
)

from volumes.api import VolumeListAPIView
from volumes.models import Volume

logger = logging.getLogger(__name__)


class StackListAPIView(generics.ListCreateAPIView):
    '''
    TODO: Add docstring
    '''
    model = Stack
    serializer_class = StackSerializer
    parser_classes = (parsers.JSONParser,)

    def get_queryset(self):
        return self.request.user.stacks.all()

    def post(self, request, *args, **kwargs):
        '''
        Overriding post to create roles and metadata objects for this Stack
        as well as generating the salt-cloud map that will be used to launch
        machines
        '''
        # set some defaults
        launch_stack = request.DATA.get('auto_launch', True)
        provision_stack = request.DATA.get('auto_provision', True)

        # check for duplicates
        title = request.DATA.get('title')
        if Stack.objects.filter(user=self.request.user, title=title).count():
            raise ResourceConflict('A Stack already exists with the given '
                                   'title.')

        # create the stack object and foreign key objects
        stack = Stack.objects.create_stack(request.user, request.DATA)

        if launch_stack:
            # Queue up stack creation and provisioning using Celery
            task_list = [
                tasks.launch_hosts.si(stack.id),
                tasks.update_metadata.si(stack.id),
                tasks.tag_infrastructure.si(stack.id),
                tasks.register_dns.si(stack.id),
                tasks.sync_all.si(stack.id)
            ]

            # provisioning is optional (mainly useful for getting machines
            # up so you can play with salt states)
            if provision_stack:
                task_list.append(tasks.provision_hosts.si(stack.id))

            # always finish
            task_list.append(tasks.finish_stack.si(stack.id))

            logger.debug(task_list)
            task_chain = reduce(or_, task_list)

            # execute the chain
            task_chain(link_error=tasks.handle_error.s(stack.id))

        # return serialized stack object
        serializer = StackSerializer(stack, context={
            'request': request,
        })
        return Response(serializer.data)


class StackDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    model = Stack
    serializer_class = StackSerializer
    parser_classes = (parsers.JSONParser,)

    def get_object(self):
        return get_object_or_404(Stack, id=self.kwargs.get('pk'),
                                 user=self.request.user)

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

    def put(self, request, *args, **kwargs):
        '''
        PUT request on a stack allows RPC-like actions to be called to
        interact with the stack. Request data is JSON, and must provide
        an `action` parameter. Actions may require additional arguments 
        which may be provided via the `args` parameter. 
        
        Valid actions: stop, start, restart, terminate
        '''

        stack = self.get_object()
        hosts = stack.get_hosts()
        host_count = hosts.count()
        action = request.DATA.get('action', None)
        args = request.DATA.get('args', [])

        if not action:
            raise BadRequest('action is a required parameter.')

        driver = stack.get_driver()
        available_actions = driver.get_available_actions()

        if action not in available_actions:
            raise BadRequest('action is not alowed. Only the following '
                             'actions are allowed: {}'.format(', '.join(available_actions)))


        # In case of a launch action, the stack must not have any available 
        # hosts (ie, the stack must have already been terminated.)
        if action == driver.ACTION_LAUNCH and host_count > 0:
            raise BadRequest('Launching a stack is only available when '
                             'the stack is in a terminated state. This '
                             'stack has %d hosts available.' % host_count)

        # All other actions require hosts to be available
        elif action != driver.ACTION_LAUNCH and host_count == 0:
            raise BadRequest('The submitted action requires the stack to have '
                             'available hosts. Perhaps you meant to run the '
                             'launch action instead.')

        # check the action against current states (e.g., starting can't happen
        # unless the hosts are in the stopped state.)
        # XXX: Assuming that host metadata is accurate here
        for host in hosts:
            if action == driver.ACTION_START and \
               host.state != driver.STATE_STOPPED:
                raise BadRequest('Start action requires all hosts to be in '
                                 'the stopped state first. At least one host '
                                 'is reporting an invalid '
                                 'state: %s' % host.state)
            if action == driver.ACTION_STOP and \
               host.state != driver.STATE_RUNNING:
                raise BadRequest('Stop action requires all hosts to be in '
                                 'the running state first. At least one host '
                                 'is reporting an invalid '
                                 'state: %s' % host.state)
            if action == driver.ACTION_TERMINATE and \
               host.state not in (driver.STATE_RUNNING, driver.STATE_STOPPED):
                raise BadRequest('Terminate action requires all hosts to be '
                                 'in the either the running or stopped state '
                                 'first. At least one host is reporting an '
                                 'invalid state: %s' % host.state)
            if action == driver.ACTION_PROVISION and \
               host.state not in (driver.STATE_RUNNING,):
                raise BadRequest('Provision action requires all hosts to be '
                                 'in the running state first. At least one '
                                 'host is reporting an '
                                 'invalid state: %s' % host.state)
            

        # Kick off the celery task for the given action
        stack.set_status(Stack.EXECUTING_ACTION, 
                         'Stack is executing action \'{0}\''.format(action))

        # Keep track of the tasks we need to run for this execution
        task_list = []

        # FIXME: not generic
        if action in (driver.ACTION_STOP, driver.ACTION_TERMINATE):
            # Unregister DNS when executing the above actions
            task_list.append(tasks.unregister_dns.si(stack.id))

        # Launch is slightly different than other actions
        if action == driver.ACTION_LAUNCH:
            task_list.append(tasks.launch_hosts.si(stack.id))

        # Terminate should leverage salt-cloud or salt gets confused about
        # the state of things
        elif action == driver.ACTION_TERMINATE:
            task_list.append(tasks.destroy_hosts.si(stack.id, delete_stack=False))

        # Execute other actions
        else:
            task_list.append(tasks.execute_action.si(stack.id, action, *args))

        # Update the metadata after the action has been executed
        task_list.append(tasks.update_metadata.si(stack.id))

        # Launching requires us to tag the newly available infrastructure
        if action in (driver.ACTION_LAUNCH,):
            tasks.tag_infrastructure.si(stack.id)

        # These actions require new DNS and provisioning
        if action in (driver.ACTION_START, driver.ACTION_LAUNCH):
            # Register DNS when executing the above actions
            task_list.append(tasks.register_dns.si(stack.id))
            # Also reprovision just in case?
            # TODO: do we need this and are there cases where special things
            # need to happen after a host is restarted?
            task_list.append(tasks.sync_all.si(stack.id))
            task_list.append(tasks.provision_hosts.si(stack.id))

        task_list.append(tasks.finish_stack.si(stack.id))

        # chain together our tasks using the bitwise or operator
        task_chain = reduce(or_, task_list)

        # Update all host states
        hosts.update(state='actioning')

        # execute the chain
        task_chain()

        serializer = self.get_serializer(stack)
        return Response(serializer.data)


class StackHistoryList(generics.ListAPIView):
    model = StackHistory
    serializer_class = StackHistorySerializer


class HostListAPIView(generics.ListAPIView):
    model = Host
    serializer_class = HostSerializer

    def get_queryset(self):
        return Host.objects.filter(stack__user=self.request.user)


class StackHostsAPIView(HostListAPIView):
    parser_classes = (parsers.JSONParser,)

    def get_queryset(self):
        return Host.objects.filter(stack__pk=self.kwargs.get('pk'),
                                   stack__user=self.request.user)

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
            tasks.tag_infrastructure.si(stack.id, host_ids=host_ids) | 
            tasks.register_dns.si(stack.id, host_ids=host_ids) | 
            tasks.sync_all.si(stack.id) |
            tasks.provision_hosts.si(stack.id, host_ids=host_ids) |
            tasks.finish_stack.si(stack.id)
        )
        
        # execute the chain
        task_chain()

        serializer = self.get_serializer(stack)
        return Response(serializer.data)

    def get(self, request, *args, **kwargs):
        '''
        Override get method to add additional host-specific info
        to the result that is looked up via salt.
        '''
        result = super(StackHostsAPIView, self).get(request, *args, **kwargs)
        if not result.data['results']:
            return result

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


class StackVolumesAPIView(VolumeListAPIView):

    def get_queryset(self):
        return Volume.objects.filter(stack__pk=self.kwargs.get('pk'))


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

