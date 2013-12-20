import logging
from collections import defaultdict
from datetime import datetime
from operator import or_

import celery
from django.shortcuts import get_object_or_404

from rest_framework import (
    generics,
    parsers,
)
from rest_framework.response import Response

from core.exceptions import (
    ResourceConflict,
    BadRequest,
)

from volumes.api import VolumeListAPIView
from volumes.models import Volume
from blueprints.models import Blueprint
from cloud.providers.base import BaseCloudProvider

from . import tasks, models, serializers, filters

logger = logging.getLogger(__name__)


class StackListAPIView(generics.ListCreateAPIView):
    '''
    TODO: Add docstring
    '''
    model = models.Stack
    serializer_class = serializers.StackSerializer
    parser_classes = (parsers.JSONParser,)
    filter_class = filters.StackFilter

    def get_queryset(self):
        return self.request.user.stacks.all()

    def create(self, request, *args, **kwargs):
        '''
        Overriding create method to build roles and metadata objects for this Stack
        as well as generating the salt-cloud map that will be used to launch
        machines
        '''
        # make sure the user has a public key or they won't be able to SSH
        # later
        if not request.user.settings.public_key:
            raise BadRequest('You have not added a public key to your user '
                             'profile and will not be able to SSH in to any '
                             'machines. Please update your user profile '
                             'before continuing.')

        # Validate data
        errors = {}
        blueprint_id = request.DATA.pop('blueprint', '')
        title = request.DATA.get('title', '')
        description = request.DATA.get('description', '')
        properties = request.DATA.get('properties', {})

        # check for required blueprint
        if not blueprint_id:
            errors.setdefault('blueprint', []).append('This field is required.')
        else:
            try:
                blueprint = Blueprint.objects.get(pk=blueprint_id,
                                                  owner=request.user)
            except Blueprint.DoesNotExist:
                errors.setdefault('blueprint', []).append(
                    'Blueprint with id {0} does not exist.'.format(blueprint_id)
                )
            except ValueError:
                errors.setdefault('blueprint', []).append(
                    'This field must be an integer ID of an existing blueprint.'
                )

        if errors:
            raise BadRequest(errors)

        # Generate the title and/or description if not provided by user 
        if not title and not description:
            extra_description = ' (Title and description'
        elif not title:
            extra_description = ' (Title'
        elif not description:
            extra_description = ' (Description'
        else:
            extra_description = ''
        if extra_description:
            extra_description += ' auto generated from Blueprint {0})'.format(blueprint.pk)

        if not title:
            request.DATA['title'] = '{0} ({1})'.format(
                blueprint.title,
                datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            )

        if not description:
            description = blueprint.description
        request.DATA['description'] = description + '{0}'.format(extra_description)

        # check for duplicates
        if models.Stack.objects.filter(owner=self.request.user, title=title).count():
            errors.setdefault('title', []).append(
                'A Stack with this title already exists in your account.'
            )

        if not isinstance(properties, dict):
            errors.setdefault('properties', []).append(
                'This field must be a JSON object.'
            )
        else:
            # user properties are not allowed to provide a __stackdio__ key
            if '__stackdio__' in properties:
                errors.setdefault('properties', []).append(
                    'The __stackdio__ key is reserved for system use.'
                )

        if errors:
            raise BadRequest(errors)

        # create the stack and related objects
        try:
            logger.debug(request.DATA)
            stack = models.Stack.objects.create_stack(request.user, blueprint, **request.DATA)
        except Exception, e:
            logger.exception(e)
            raise BadRequest(str(e))

        # set some defaults
        launch_stack = request.DATA.get('auto_launch', True)
        provision_stack = request.DATA.get('auto_provision', True)

        if launch_stack:
            # Queue up stack creation and provisioning using Celery
            task_list = [
                tasks.launch_hosts.si(stack.id),
                tasks.update_metadata.si(stack.id),
                tasks.tag_infrastructure.si(stack.id),
                tasks.register_dns.si(stack.id),
                tasks.ping.si(stack.id),
                tasks.sync_all.si(stack.id)
            ]

            # provisioning is optional (mainly useful for getting machines
            # up so you can play with salt states)
            if provision_stack:
                task_list.append(tasks.highstate.si(stack.id))
                task_list.append(tasks.orchestrate.si(stack.id))

            # always finish
            task_list.append(tasks.finish_stack.si(stack.id))

            logger.debug(task_list)
            task_chain = reduce(or_, task_list)

            # execute the chain
            stack.set_status('queued', 'Stack has been submitted to launch queue.')
            task_chain(link_error=tasks.handle_error.s(stack.id))

        # return serialized stack object
        serializer = serializers.StackSerializer(stack, context={
            'request': request,
        })
        return Response(serializer.data)


class StackDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    model = models.Stack
    serializer_class = serializers.StackSerializer
    parser_classes = (parsers.JSONParser,)

    def get_object(self):
        return get_object_or_404(models.Stack, id=self.kwargs.get('pk'),
                                 owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        '''
        Overriding the delete method to make sure the stack
        is taken offline before being deleted
        '''
        # Update the status
        stack = self.get_object()
        msg = 'Stack will be removed upon successful termination ' \
              'of all machines'
        stack.set_status(models.Stack.DESTROYING, msg)

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


class StackPropertiesAPIView(generics.RetrieveUpdateAPIView):

    model = models.Stack
    serializer_class = serializers.StackPropertiesSerializer
    parser_classes = (parsers.JSONParser,)

    def get_object(self):
        return get_object_or_404(models.Stack, id=self.kwargs.get('pk'),
                                 owner=self.request.user)

    def update(self, request, *args, **kwargs):
        stack = self.get_object()

        if not isinstance(request.DATA, dict):
            raise BadRequest('Data must be JSON object of properties.')

        if not request.DATA:
            raise BadRequest('No properties were given.')
        
        # update the stack properties
        stack.properties = request.DATA
        return Response(stack.properties)


class StackActionAPIView(generics.SingleObjectAPIView):

    serializer_class = serializers.StackSerializer

    def get_object(self):
        return get_object_or_404(models.Stack, id=self.kwargs.get('pk'),
                                 owner=self.request.user)

    def post(self, request, *args, **kwargs):
        '''
        POST request allows RPC-like actions to be called to interact
        with the stack. Request contains JSON with an `action` parameter
        and optional `args` depending on the action being executed.

        Valid actions: stop, start, restart, terminate, provision
        '''

        stack = self.get_object()
        driver_hosts_map = stack.get_driver_hosts_map()
        total_host_count = len(stack.get_hosts().exclude(instance_id=''))
        action = request.DATA.get('action', None)
        args = request.DATA.get('args', [])

        if not action:
            raise BadRequest('action is a required parameter.')

        
        # check the individual provider for available actions
        for driver, hosts in driver_hosts_map.iteritems():
            available_actions = driver.get_available_actions()
            if action not in available_actions:
                raise BadRequest('At least one of the hosts in this stack does '
                                 'not support the requested action.')

        # In case of a launch action, the stack must not have any available 
        # hosts (ie, the stack must have already been terminated.)
        if action == BaseCloudProvider.ACTION_LAUNCH and total_host_count > 0:
            raise BadRequest('Launching a stack is only available when '
                             'the stack is in a terminated state. This '
                             'stack has %d hosts available.' % total_host_count)

        # All other actions require hosts to be available
        elif action != BaseCloudProvider.ACTION_LAUNCH and total_host_count == 0:
            raise BadRequest('The submitted action requires the stack to have '
                             'available hosts. Perhaps you meant to run the '
                             'launch action instead.')

        # Hosts may be spread accross different providers, so we need to 
        # handle them differently based on the provider and its implementation
        driver_hosts_map = stack.get_driver_hosts_map()
        for driver, hosts in driver_hosts_map.iteritems():

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
        stack.set_status(models.Stack.EXECUTING_ACTION, 
                         'Stack is executing action \'{0}\''.format(action))

        # Keep track of the tasks we need to run for this execution
        task_list = []

        # FIXME: not generic
        if action in (BaseCloudProvider.ACTION_STOP, BaseCloudProvider.ACTION_TERMINATE):
            # Unregister DNS when executing the above actions
            task_list.append(tasks.unregister_dns.si(stack.id))

        # Launch is slightly different than other actions
        if action == BaseCloudProvider.ACTION_LAUNCH:
            task_list.append(tasks.launch_hosts.si(stack.id))

        # Terminate should leverage salt-cloud or salt gets confused about
        # the state of things
        elif action == BaseCloudProvider.ACTION_TERMINATE:
            task_list.append(tasks.destroy_hosts.si(stack.id, delete_stack=False))

        elif action == BaseCloudProvider.ACTION_PROVISION:
            # action that gets handled later
            pass

        # Execute other actions that may be available on the driver
        else:
            task_list.append(tasks.execute_action.si(stack.id, action, *args))

        # Update the metadata after the action has been executed
        if action != BaseCloudProvider.ACTION_TERMINATE:
            task_list.append(tasks.update_metadata.si(stack.id))

        # Launching requires us to tag the newly available infrastructure
        if action in (BaseCloudProvider.ACTION_LAUNCH,):
            tasks.tag_infrastructure.si(stack.id)

        # Starting and launching requires DNS updates
        if action in (BaseCloudProvider.ACTION_START, BaseCloudProvider.ACTION_LAUNCH):
            task_list.append(tasks.register_dns.si(stack.id))

        # starting, launching, or reprovisioning requires us to execute the provisioning
        # tasks
        if action in (BaseCloudProvider.ACTION_START, BaseCloudProvider.ACTION_LAUNCH, BaseCloudProvider.ACTION_PROVISION):
            task_list.append(tasks.ping.si(stack.id))
            task_list.append(tasks.sync_all.si(stack.id))
            task_list.append(tasks.highstate.si(stack.id))
            task_list.append(tasks.orchestrate.si(stack.id))

        task_list.append(tasks.finish_stack.si(stack.id))

        # chain together our tasks using the bitwise or operator
        task_chain = reduce(or_, task_list)

        # Update all host states
        stack.get_hosts().update(state='actioning')

        # execute the chain
        task_chain()

        serializer = self.get_serializer(stack)
        return Response(serializer.data)


class StackHistoryList(generics.ListAPIView):
    model = models.StackHistory
    serializer_class = serializers.StackHistorySerializer


class HostListAPIView(generics.ListAPIView):
    model = models.Host
    serializer_class = serializers.HostSerializer

    def get_queryset(self):
        return models.Host.objects.filter(stack__owner=self.request.user)


class StackHostsAPIView(HostListAPIView):
    parser_classes = (parsers.JSONParser,)

    def get_queryset(self):
        return models.Host.objects.filter(stack__pk=self.kwargs.get('pk'),
                                   stack__owner=self.request.user)

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
            tasks.ping.si(stack.id) |
            tasks.sync_all.si(stack.id) |
            tasks.highstate.si(stack.id, host_ids=host_ids) |
            tasks.orchestrate.si(stack.id, host_ids=host_ids) |
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
    model = models.Host
    serializer_class = serializers.HostSerializer

    def destroy(self, request, *args, **kwargs):
        '''
        Override the delete method to first terminate the host
        before destroying the object.
        '''
        # get the stack id for the host
        host = self.get_object()
        volume_ids = [v.id for v in host.volumes.all()]

        host.set_status(models.Host.DELETING, 'Deleting host.')

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

