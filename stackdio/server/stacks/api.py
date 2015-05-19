# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import StringIO
import logging
import zipfile
from datetime import datetime
from operator import or_
from os import listdir
from os.path import join, isfile

import envoy
import yaml
from django.http import HttpResponse
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import DjangoFilterBackend, DjangoObjectPermissionsFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.reverse import reverse

from blueprints.models import BlueprintHostDefinition
from cloud.filters import SecurityGroupFilter
from cloud.providers.base import BaseCloudProvider
from core.exceptions import BadRequest
from core.permissions import StackdioDjangoObjectPermissions
from core.renderers import PlainTextRenderer
from volumes.serializers import VolumeSerializer
from . import filters, models, serializers, tasks, validators, workflows


logger = logging.getLogger(__name__)


class PublicStackMixin(object):
    def get_object(self):
        queryset = models.Stack.objects.all()

        obj = get_object_or_404(queryset, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj


class StackActionObjectPermissions(StackdioDjangoObjectPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.view_%(model_name)s'],
        'PUT': ['%(app_label)s.view_%(model_name)s'],
        'PATCH': ['%(app_label)s.view_%(model_name)s'],
        'DELETE': ['%(app_label)s.view_%(model_name)s'],
    }


def filter_actions(user, stack, actions):
    ret = []
    for action in actions:
        the_action = action
        if action == 'custom':
            the_action = 'execute'
        if user.has_perm('stacks.{0}_stack'.format(the_action.lower()), stack):
            ret.append(action)

    return ret


class StackListAPIView(generics.ListCreateAPIView):
    """
    Displays a list of all stacks visible to you.
    """
    queryset = models.Stack.objects.all()
    serializer_class = serializers.StackSerializer
    filter_backends = (DjangoFilterBackend, DjangoObjectPermissionsFilter)
    filter_class = filters.StackFilter

    def perform_create(self, serializer):
        """
        Overriding create method to build roles and metadata objects for this
        Stack as well as generating the salt-cloud map that will be used to
        launch machines
        """

        # make sure the user has a public key or they won't be able to SSH
        # later
        if not self.request.user.settings.public_key:
            raise BadRequest('You have not added a public key to your user '
                             'profile and will not be able to SSH in to any '
                             'machines. Please update your user profile '
                             'before continuing.')

        serializer.save(owner=self.request.user)


class StackDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Stack.objects.all()
    serializer_class = serializers.StackSerializer

    def destroy(self, request, *args, **kwargs):
        """
        Overriding the delete method to make sure the stack
        is taken offline before being deleted.  The default delete method
        returns a 204 status and we want to return a 200 with the serialized
        object
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_destroy(self, stack):
        # Update the status
        if stack.status not in models.Stack.SAFE_STATES:
            raise BadRequest('You may not delete this stack in its '
                             'current state.  Please wait until it is finished '
                             'with the current action.')

        msg = 'Stack will be removed upon successful termination of all machines'
        stack.set_status(models.Stack.DESTROYING,
                         models.Stack.DESTROYING, msg)
        parallel = self.request.DATA.get('parallel', True)

        # Execute the workflow
        workflow = workflows.DestroyStackWorkflow(stack)
        workflow.opts.parallel = parallel
        workflow.execute()


class StackPropertiesAPIView(PublicStackMixin, generics.RetrieveUpdateAPIView):
    queryset = models.Stack.objects.all()
    serializer_class = serializers.StackPropertiesSerializer


class StackHistoryAPIView(PublicStackMixin, generics.ListAPIView):
    queryset = models.Stack.objects.all()
    serializer_class = serializers.StackHistorySerializer

    def get_queryset(self):
        stack = self.get_object()
        return stack.history.all()


class StackActionAPIView(PublicStackMixin, generics.GenericAPIView):
    queryset = models.Stack.objects.all()
    serializer_class = serializers.StackSerializer
    permission_classes = (permissions.IsAuthenticated, StackActionObjectPermissions)

    def get(self, request, *args, **kwargs):
        stack = self.get_object()
        driver_hosts_map = stack.get_driver_hosts_map()
        available_actions = set()
        for driver, hosts in driver_hosts_map.iteritems():
            available_actions.update(driver.get_available_actions())

        available_actions = filter_actions(request.user, stack, available_actions)

        return Response({
            'available_actions': sorted(available_actions),
        })

    # TODO: Code complexity issues are ignored for now
    def post(self, request, *args, **kwargs):  # NOQA
        """
        POST request allows RPC-like actions to be called to interact
        with the stack. Request contains JSON with an `action` parameter
        and optional `args` depending on the action being executed.

        Valid actions: stop, start, restart, terminate, provision,
        orchestrate
        """

        stack = self.get_object()

        if stack.status not in models.Stack.SAFE_STATES:
            raise BadRequest('You may not perform an action while the '
                             'stack is in its current state.')

        driver_hosts_map = stack.get_driver_hosts_map()
        total_host_count = len(stack.get_hosts().exclude(instance_id=''))
        action = request.DATA.get('action', None)
        args = request.DATA.get('args', [])

        if not action:
            raise BadRequest('action is a required parameter.')

        available_actions = set()

        # check the individual provider for available actions
        for driver, hosts in driver_hosts_map.iteritems():
            host_available_actions = driver.get_available_actions()
            if action not in host_available_actions:
                raise BadRequest('At least one of the hosts in this stack '
                                 'does not support the requested action.')
            available_actions.update(host_available_actions)

        if action not in filter_actions(request.user, stack, available_actions):
            raise PermissionDenied(
                'You are not authorized to execute the "{0}" action on this stack'.format(action)
            )

        # All actions other than launch require hosts to be available
        if action != BaseCloudProvider.ACTION_LAUNCH and total_host_count == 0:
            raise BadRequest('The submitted action requires the stack to have '
                             'available hosts. Perhaps you meant to run the '
                             'launch action instead.')

        # Hosts may be spread accross different providers, so we need to
        # handle them differently based on the provider and its implementation
        driver_hosts_map = stack.get_driver_hosts_map()
        for driver, hosts in driver_hosts_map.iteritems():

            # check the action against current states (e.g., starting can't
            # happen unless the hosts are in the stopped state.)
            # XXX: Assuming that host metadata is accurate here
            for host in hosts:
                if action == driver.ACTION_START and host.state != driver.STATE_STOPPED:
                    raise BadRequest('Start action requires all hosts to be '
                                     'in the stopped state first. At least '
                                     'one host is reporting an invalid state: '
                                     '{0}'.format(host.state))
                if action == driver.ACTION_STOP and host.state != driver.STATE_RUNNING:
                    raise BadRequest('Stop action requires all hosts to be in '
                                     'the running state first. At least one '
                                     'host is reporting an invalid state: '
                                     '{0}'.format(host.state))
                if action == driver.ACTION_TERMINATE and host.state not in (driver.STATE_RUNNING,
                                                                            driver.STATE_STOPPED):
                    raise BadRequest('Terminate action requires all hosts to '
                                     'be in the either the running or stopped '
                                     'state first. At least one host is '
                                     'reporting an invalid state: {0}'
                                     .format(host.state))
                if (
                                    action == driver.ACTION_PROVISION or
                                    action == driver.ACTION_ORCHESTRATE or
                                action == driver.ACTION_CUSTOM
                ) and host.state not in (driver.STATE_RUNNING,):
                    raise BadRequest(
                        'Provisioning actions require all hosts to be in the '
                        'running state first. At least one host is reporting '
                        'an invalid state: {0}'.format(host.state))

        # Kick off the celery task for the given action
        stack.set_status(models.Stack.EXECUTING_ACTION,
                         models.Stack.PENDING,
                         'Stack is executing action \'{0}\''.format(action))

        if action == BaseCloudProvider.ACTION_CUSTOM:

            task_list = []

            action_ids = []

            for command in args:
                action = models.StackAction(stack=stack)
                action.host_target = command['host_target']
                action.command = command['command']
                action.type = BaseCloudProvider.ACTION_CUSTOM
                action.start = datetime.now()
                action.save()

                action_ids.append(action.id)

                task_list.append(tasks.custom_action.si(
                    action.id,
                    command['host_target'],
                    command['command']
                ))

            task_chain = reduce(or_, task_list)

            task_chain()

            ret = {
                "results_urls": []
            }

            for action_id in action_ids:
                ret['results_urls'].append(reverse(
                    'stackaction-detail',
                    kwargs={
                        'pk': action_id,
                    },
                    request=request
                ))

            return Response(ret)

        # Keep track of the tasks we need to run for this execution
        task_list = []

        # FIXME: not generic
        if action in (BaseCloudProvider.ACTION_STOP,
                      BaseCloudProvider.ACTION_TERMINATE):
            # Unregister DNS when executing the above actions
            task_list.append(tasks.unregister_dns.si(stack.id))

        # Launch is slightly different than other actions
        if action == BaseCloudProvider.ACTION_LAUNCH:
            task_list.append(tasks.launch_hosts.si(stack.id))
            task_list.append(tasks.update_metadata.si(stack.id))
            task_list.append(tasks.cure_zombies.si(stack.id))

        # Terminate should leverage salt-cloud or salt gets confused about
        # the state of things
        elif action == BaseCloudProvider.ACTION_TERMINATE:
            task_list.append(
                tasks.destroy_hosts.si(stack.id,
                                       delete_hosts=False,
                                       delete_security_groups=False)
            )

        elif action in (BaseCloudProvider.ACTION_PROVISION,
                        BaseCloudProvider.ACTION_ORCHESTRATE,):
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
        if action in (BaseCloudProvider.ACTION_START,
                      BaseCloudProvider.ACTION_LAUNCH):
            task_list.append(tasks.register_dns.si(stack.id))

        # starting, launching, or reprovisioning requires us to execute the
        # provisioning tasks
        if action in (BaseCloudProvider.ACTION_START,
                      BaseCloudProvider.ACTION_LAUNCH,
                      BaseCloudProvider.ACTION_PROVISION,
                      BaseCloudProvider.ACTION_ORCHESTRATE):
            task_list.append(tasks.ping.si(stack.id))
            task_list.append(tasks.sync_all.si(stack.id))

        if action in (BaseCloudProvider.ACTION_START,
                      BaseCloudProvider.ACTION_LAUNCH,
                      BaseCloudProvider.ACTION_PROVISION):
            task_list.append(tasks.highstate.si(stack.id))
            task_list.append(tasks.global_orchestrate.si(stack.id))
            task_list.append(tasks.orchestrate.si(stack.id))

        if action == BaseCloudProvider.ACTION_ORCHESTRATE:
            task_list.append(tasks.orchestrate.si(stack.id, 2))

        task_list.append(tasks.finish_stack.si(stack.id))

        # chain together our tasks using the bitwise or operator
        task_chain = reduce(or_, task_list)

        # execute the chain
        task_chain()

        # Update all host states
        stack.get_hosts().update(state='actioning')

        serializer = self.get_serializer(stack)
        return Response(serializer.data)


class StackActionListAPIView(PublicStackMixin, generics.ListAPIView):
    queryset = models.Stack.objects.all()
    serializer_class = serializers.StackActionSerializer

    def get_queryset(self):
        stack = self.get_object()
        return models.StackAction.objects.filter(stack=stack)


class StackActionDetailAPIView(generics.RetrieveDestroyAPIView):
    queryset = models.StackAction.objects.all()
    serializer_class = serializers.StackActionSerializer


@api_view(['GET'])
def stack_action_zip(request, pk):
    actions = models.StackAction.objects.filter(pk=pk)
    if len(actions) is 1:
        action = actions[0]

        if len(action.std_out()) is 0:
            return Response({"detail": "Not found"})

        file_buffer = StringIO.StringIO()
        action_zip = zipfile.ZipFile(file_buffer, 'w')

        filename = 'action_output_' + \
                   action.submit_time().strftime('%Y%m%d_%H%M%S')

        action_zip.writestr(
            str('{0}/__command'.format(filename)),
            str(action.command))

        for output in action.std_out():
            action_zip.writestr(
                str('{0}/{1}.txt'.format(filename, output['host'])),
                str(output['output']))

        action_zip.close()

        response = HttpResponse(file_buffer.getvalue(),
            content_type='application/zip')
        response['Content-Disposition'] = (
            'attachment; filename={0}.zip'.format(filename)
        )
        return response
    else:
        return Response({"detail": "Not found"})


class HostListAPIView(generics.ListAPIView):
    queryset = models.Host.objects.all()
    serializer_class = serializers.HostSerializer
    filter_backends = (DjangoFilterBackend, DjangoObjectPermissionsFilter)


class StackHostsAPIView(PublicStackMixin, generics.ListAPIView):
    queryset = models.Stack.objects.all()
    serializer_class = serializers.HostSerializer

    def get_queryset(self):
        stack = self.get_object()
        return stack.hosts.all()

    def post(self, request, *args, **kwargs):
        """
        Overriding POST for a stack to be able to add or remove
        hosts from the stack. Both actions are dependent on
        a blueprint host definition in the blueprint used to
        launch the stack.

        POST /api/stacks/<stack_id>/hosts/
        Allows users to add or remove hosts on a running stack. The action is
        specified along with a list of objects specifying what hosts to add or
        remove, which implies that only a single type of action may be used
        at one time.

        {
            "action": "<action>",
            "args": [
                {
                    "host_definition": <int>,
                    "count": <int>,
                    "backfill": <bool>
                },
                ...
                ...
                {
                    "host_definition": <int>,
                    "count": <int>,
                    "backfill": <bool>
                }
            ]
        }

        where:

        @param action (string) REQUIRED; what type of action to take on the
            stack, must be one of 'add' or 'remove'
        @param count (int) REQUIRED; how many additional hosts to add or remove
        @param host_definition (int) REQUIRED; the id of a blueprint host
            definition that is part of the blueprint the stack was initially
            launched from
        @param backfill (bool) OPTIONAL DEFAULT=false; if true, the hostnames
            will be generated in a way to fill in any gaps in the existing
            hostnames of the stack. For example, if your stack has a host list
            [foo-1, foo-3, foo-4] and you ask for three additional hosts, the
            resulting set of hosts is [foo-1, foo-2, foo-3, foo4, foo-5, foo-6]
        """
        errors = validators.StackAddRemoveHostsValidator(request).validate()
        if errors:
            raise BadRequest(errors)

        action = request.DATA['action']

        if action == 'add':
            return self.add_hosts(request)
        elif action == 'remove':
            return self.remove_hosts(request)

    def add_hosts(self, request):
        stack = self.get_object()
        args = request.DATA['args']

        created_hosts = []
        for arg in args:
            hostdef = BlueprintHostDefinition.objects.get(
                pk=arg['host_definition']
            )
            count = arg['count']
            backfill = arg.get('backfill', False)

            hosts = stack.create_hosts(host_definition=hostdef,
                                       count=count,
                                       backfill=backfill)
            created_hosts.extend(hosts)

        if created_hosts:
            host_ids = [h.id for h in created_hosts]

            # regnerate the map file and run the standard set of launch tasks
            stack._generate_map_file()
            workflows.LaunchWorkflow(stack, host_ids=host_ids).execute()

        serializer = self.get_serializer(created_hosts, many=True)
        return Response(serializer.data)

    def remove_hosts(self, request):
        stack = self.get_object()
        args = request.DATA['args']

        hosts = []
        for arg in args:
            hostdef = BlueprintHostDefinition.objects.get(
                pk=arg['host_definition']
            )
            count = arg['count']

            logger.debug(arg)
            logger.debug(hostdef)

            hosts.extend(
                stack.hosts.filter(blueprint_host_definition=hostdef).order_by('-index')[:count]
            )

        logger.debug('Hosts to remove: {0}'.format(hosts))
        host_ids = [h.pk for h in hosts]
        if host_ids:
            models.Host.objects.filter(pk__in=host_ids).update(
                state=models.Host.DELETING,
                state_reason='User initiated delete.'
            )
            workflows.DestroyHostsWorkflow(stack, host_ids).execute()
        else:
            raise BadRequest('No hosts were found to remove.')
        return Response({})

    def get(self, request, *args, **kwargs):
        """
        Override get method to add additional host-specific info
        to the result that is looked up via salt when user requests it
        """
        provider_metadata = request.QUERY_PARAMS.get('provider_metadata') == 'true'
        result = super(StackHostsAPIView, self).get(request, *args, **kwargs)

        if not provider_metadata or not result.data['results']:
            return result

        stack = self.get_object()
        query_results = stack.query_hosts()

        # TODO: query_results are highly dependent on the underlying
        # salt-cloud driver and there's no guarantee that the result
        # format for AWS will be the same for Rackspace. In the future,
        # we should probably pass the results off to the cloud provider
        # implementation to format into a generic result for the user
        for host in result.data['results']:
            hostname = host['hostname']
            host['provider_metadata'] = query_results[hostname]

        return result


class StackVolumesAPIView(PublicStackMixin, generics.ListAPIView):
    queryset = models.Stack.objects.all()
    serializer_class = VolumeSerializer

    def get_queryset(self):
        stack = self.get_object()
        return stack.volumes.all()


class HostDetailAPIView(generics.RetrieveDestroyAPIView):
    queryset = models.Host.objects.all()
    serializer_class = serializers.HostSerializer

    def destroy(self, request, *args, **kwargs):
        """
        Override the delete method to first terminate the host
        before destroying the object.
        """
        # get the stack id for the host
        host = self.get_object()
        host.set_status(models.Host.DELETING, 'Deleting host.')

        stack = host.stack
        host_ids = [host.pk]

        # unregister DNS and destroy the host
        workflows.DestroyHostsWorkflow(stack, host_ids).execute()

        # Return the host while its deleting
        serializer = self.get_serializer(host)
        return Response(serializer.data)


class StackFQDNListAPIView(PublicStackMixin, generics.GenericAPIView):
    queryset = models.Stack.objects.all()

    def get(self, request, *args, **kwargs):
        stack = self.get_object()
        fqdns = [h.fqdn for h in stack.hosts.all()]
        return Response(fqdns)


class StackLogsAPIView(PublicStackMixin, generics.GenericAPIView):
    queryset = models.Stack.objects.all()

    def get(self, request, *args, **kwargs):
        stack = self.get_object()
        log_dir = stack.get_log_directory()
        return Response({
            'latest': {
                'launch': reverse(
                    'stack-logs-detail',
                    kwargs={
                        'pk': stack.pk,
                        'log': 'launch.log.latest'},
                    request=request),
                'provisioning': reverse(
                    'stack-logs-detail',
                    kwargs={
                        'pk': stack.pk,
                        'log': 'provisioning.log.latest'},
                    request=request),
                'provisioning-error': reverse(
                    'stack-logs-detail',
                    kwargs={
                        'pk': stack.pk,
                        'log': 'provisioning.err.latest'},
                    request=request),
                'global_orchestration': reverse(
                    'stack-logs-detail',
                    kwargs={
                        'pk': stack.pk,
                        'log': 'global_orchestration.log.latest'},
                    request=request),
                'global_orchestration-error': reverse(
                    'stack-logs-detail',
                    kwargs={
                        'pk': stack.pk,
                        'log': 'global_orchestration.err.latest'},
                    request=request),
                'orchestration': reverse(
                    'stack-logs-detail',
                    kwargs={
                        'pk': stack.pk,
                        'log': 'orchestration.log.latest'},
                    request=request),
                'orchestration-error': reverse(
                    'stack-logs-detail',
                    kwargs={
                        'pk': stack.pk,
                        'log': 'orchestration.err.latest'},
                    request=request),
            },
            'historical': [
                reverse('stack-logs-detail',
                        kwargs={
                            'pk': stack.pk,
                            'log': log,
                        },
                        request=request)
                for log in sorted(listdir(log_dir))

            ]
        })


class StackProvisioningErrorsAPIView(PublicStackMixin, generics.GenericAPIView):
    queryset = models.Stack.objects.all()

    def get(self, request, *args, **kwargs):
        stack = self.get_object()
        err_file = join(stack.get_root_directory(), 'provisioning.err.latest')
        if not isfile(err_file):
            raise BadRequest('No error file found for this stack. Has '
                             'provisioning occurred yet?')

        with open(err_file) as f:
            err_yaml = yaml.safe_load(f)
        return Response(err_yaml)


class StackOrchestrationErrorsAPIView(PublicStackMixin, generics.GenericAPIView):
    queryset = models.Stack.objects.all()

    def get(self, request, *args, **kwargs):
        stack = self.get_object()
        err_file = join(stack.get_root_directory(), 'orchestration.err.latest')
        if not isfile(err_file):
            raise BadRequest('No error file found for this stack. Has '
                             'orchestration occurred yet?')

        with open(err_file) as f:
            err_yaml = yaml.safe_load(f)
        return Response(err_yaml)


class StackLogsDetailAPIView(StackLogsAPIView):
    queryset = models.Stack.objects.all()
    renderer_classes = (PlainTextRenderer,)

    # TODO: Code complexity ignored for now
    def get(self, request, *args, **kwargs):  # NOQA
        stack = self.get_object()
        log_file = self.kwargs.get('log', '')

        try:
            tail = int(request.QUERY_PARAMS.get('tail', 0))
        except ValueError:
            tail = None

        try:
            head = int(request.QUERY_PARAMS.get('head', 0))
        except ValueError:
            head = None

        if head and tail:
            return Response('Both head and tail may not be used.',
                            status=status.HTTP_400_BAD_REQUEST)

        if log_file.endswith('.latest'):
            log = join(stack.get_root_directory(), log_file)
        elif log_file.endswith('.log') or log_file.endswith('.err'):
            log = join(stack.get_log_directory(), log_file)
        else:
            log = None

        if not log or not isfile(log):
            return Response('Log file does not exist: {0}.'.format(log_file),
                            status=status.HTTP_400_BAD_REQUEST)

        if tail:
            ret = envoy.run('tail -{0} {1}'.format(tail, log)).std_out
        elif head:
            ret = envoy.run('head -{0} {1}'.format(head, log)).std_out
        else:
            with open(log, 'r') as f:
                ret = f.read()
        return Response(ret)


class StackSecurityGroupsAPIView(PublicStackMixin, generics.ListAPIView):
    queryset = models.Stack.objects.all()
    serializer_class = serializers.StackSecurityGroupSerializer
    filter_class = SecurityGroupFilter

    def get_queryset(self):
        stack = self.get_object()
        return stack.get_security_groups()
