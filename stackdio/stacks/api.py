import logging
from datetime import datetime
from operator import or_
from os import listdir
from os.path import join, isfile

import envoy
import yaml
import zipfile
import StringIO
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from rest_framework import (
    generics,
    parsers,
    permissions,
    status,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from rest_framework.decorators import api_view

from core.exceptions import BadRequest
from core.renderers import PlainTextRenderer
from core.permissions import (
    AdminOrOwnerPermission, 
    AdminOrOwnerOrPublicPermission,
)
from volumes.api import VolumeListAPIView
from volumes.models import Volume
from blueprints.models import Blueprint, BlueprintHostDefinition
from cloud.providers.base import BaseCloudProvider
from cloud.models import SecurityGroup

from . import tasks, models, serializers, filters, validators, workflows

logger = logging.getLogger(__name__)


class PublicStackMixin(object):
    permission_classes = (permissions.IsAuthenticated,
                          AdminOrOwnerOrPublicPermission,)

    def get_object(self):
        obj = get_object_or_404(models.Stack, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj


class StackPublicListAPIView(generics.ListAPIView):
    model = models.Stack
    serializer_class = serializers.StackSerializer

    def get_queryset(self):
        return self.model.objects \
            .filter(public=True) \
            .exclude(owner=self.request.user)


class StackAdminListAPIView(generics.ListAPIView):
    """
    TODO: Add docstring
    """
    model = models.Stack
    serializer_class = serializers.StackSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return self.model.objects.exclude(owner=self.request.user)


class StackListAPIView(generics.ListCreateAPIView):
    """
    TODO: Add docstring
    """
    model = models.Stack
    serializer_class = serializers.StackSerializer
    parser_classes = (parsers.JSONParser,)
    filter_class = filters.StackFilter

    ALLOWED_FIELDS = ('blueprint', 'title', 'description', 'properties',
                      'max_retries', 'namespace', 'auto_launch',
                      'auto_provision', 'parallel', 'public',
                      'simulate_launch_failures', 'simulate_zombies',
                      'simulate_ssh_failures', 'failure_percent',)

    def get_queryset(self):
        return self.request.user.stacks.all()

    # TODO: Code complexity issues are ignored for now
    def create(self, request, *args, **kwargs):  # NOQA
        """
        Overriding create method to build roles and metadata objects for this
        Stack as well as generating the salt-cloud map that will be used to
        launch machines
        """
        # make sure the user has a public key or they won't be able to SSH
        # later
        if not request.user.settings.public_key:
            raise BadRequest('You have not added a public key to your user '
                             'profile and will not be able to SSH in to any '
                             'machines. Please update your user profile '
                             'before continuing.')

        # Validate data
        errors = {}

        for k in request.DATA:
            if k not in self.ALLOWED_FIELDS:
                errors.setdefault('unknown_fields', []) \
                    .append('{0} is an unknown field.'.format(k))
        if errors:
            raise BadRequest(errors)

        # REQUIRED PARAMS
        blueprint_id = request.DATA.pop('blueprint', '')
        title = request.DATA.get('title', '')
        description = request.DATA.get('description', '')

        # OPTIONAL PARAMS
        properties = request.DATA.get('properties', {})
        max_retries = request.DATA.get('max_retries', 2)

        # UNDOCUMENTED PARAMS
        # Skips launching if set to False
        launch_stack = request.DATA.get('auto_launch', True)

        # Launches in parallel mode if set to True
        parallel = request.DATA.get('parallel', True)

        # See stacks.tasks::launch_hosts for information on these params
        simulate_launch_failures = request.DATA.get('simulate_launch_failures',
                                                    False)
        simulate_ssh_failures = request.DATA.get('simulate_ssh_failures',
                                                 False)
        simulate_zombies = request.DATA.get('simulate_zombies', False)
        failure_percent = request.DATA.get('failure_percent', 0.3)

        # check for required blueprint
        if not blueprint_id:
            errors.setdefault('blueprint', []) \
                .append('This field is required.')
        else:
            try:
                blueprint = Blueprint.objects.get(pk=blueprint_id,
                                                  owner=request.user)
            except Blueprint.DoesNotExist:
                errors.setdefault('blueprint', []).append(
                    'Blueprint with id {0} does not exist.'.format(
                        blueprint_id))
            except ValueError:
                errors.setdefault('blueprint', []).append(
                    'This field must be an ID of an existing blueprint.')

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
            extra_description += ' auto generated from Blueprint {0})' \
                .format(blueprint.pk)

        if not title:
            request.DATA['title'] = '{0} ({1})'.format(
                blueprint.title,
                datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            )

        if not description:
            description = blueprint.description
        request.DATA['description'] = description + '{0}' \
            .format(extra_description)

        # check for duplicates
        if models.Stack.objects.filter(owner=self.request.user,
                                       title=title).count():
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

        # check for hostname collisions if namespace is provided
        namespace = request.DATA.get('namespace')
        if namespace:
            hostdefs = blueprint.host_definitions.all()
            hostnames = models.get_hostnames_from_hostdefs(
                hostdefs,
                username=request.user.username,
                namespace=namespace)

            # query for existing host names
            hosts = models.Host.objects.filter(hostname__in=hostnames)
            if hosts.count():
                errors.setdefault('duplicate_hostnames', []).extend(
                    [h.hostname for h in hosts]
                )

        if errors:
            raise BadRequest(errors)

        # create the stack and related objects
        try:
            logger.debug(request.DATA)
            stack = models.Stack.objects.create_stack(request.user,
                                                      blueprint,
                                                      **request.DATA)
        except Exception, e:
            logger.exception(e)
            raise BadRequest(str(e))

        if launch_stack:
            workflow = workflows.LaunchWorkflow(stack)
            workflow.opts.parallel = parallel
            workflow.opts.max_retries = max_retries
            workflow.opts.simulate_launch_failures = simulate_launch_failures
            workflow.opts.simulate_ssh_failures = simulate_ssh_failures
            workflow.opts.simulate_zombies = simulate_zombies
            workflow.opts.failure_percent = failure_percent
            workflow.execute()

            stack.set_status('queued',
                             'Stack has been submitted to launch queue.')

        # return serialized stack object
        serializer = serializers.StackSerializer(stack, context={
            'request': request,
        })
        return Response(serializer.data)


class StackDetailAPIView(PublicStackMixin,
                         generics.RetrieveUpdateDestroyAPIView):
    model = models.Stack
    serializer_class = serializers.StackSerializer
    parser_classes = (parsers.JSONParser,)

    def destroy(self, request, *args, **kwargs):
        """
        Overriding the delete method to make sure the stack
        is taken offline before being deleted
        """
        # Update the status
        stack = self.get_object()
        msg = 'Stack will be removed upon successful termination ' \
              'of all machines'
        stack.set_status(models.Stack.DESTROYING, msg)
        parallel = request.DATA.get('parallel', True)

        # Execute the workflow
        workflow = workflows.DestroyStackWorkflow(stack)
        workflow.opts.parallel = parallel
        workflow.execute()

        # Return the stack while its deleting
        serializer = self.get_serializer(stack)
        return Response(serializer.data)


class StackPropertiesAPIView(PublicStackMixin, generics.RetrieveUpdateAPIView):
    model = models.Stack
    serializer_class = serializers.StackPropertiesSerializer
    parser_classes = (parsers.JSONParser,)

    def update(self, request, *args, **kwargs):
        stack = self.get_object()

        if not isinstance(request.DATA, dict):
            raise BadRequest('Data must be JSON object of properties.')

        if not request.DATA:
            raise BadRequest('No properties were given.')

        # update the stack properties
        stack.properties = request.DATA
        return Response(stack.properties)


class StackHistoryAPIView(PublicStackMixin, generics.ListAPIView):
    model = models.StackHistory
    serializer_class = serializers.StackHistorySerializer

    def get_queryset(self):
        stack = self.get_object()
        return stack.history.all()


class StackActionAPIView(generics.SingleObjectAPIView):
    model = models.Stack
    serializer_class = serializers.StackSerializer
    permission_classes = (permissions.IsAuthenticated,
                          AdminOrOwnerPermission,)

    def get_object(self):
        obj = get_object_or_404(models.Stack, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        stack = self.get_object()
        driver_hosts_map = stack.get_driver_hosts_map()
        available_actions = set()
        for driver, hosts in driver_hosts_map.iteritems():
            available_actions.update(driver.get_available_actions())

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
                raise BadRequest('At least one of the hosts in this stack '
                                 'does not support the requested action.')

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
                if action == driver.ACTION_START and \
                   host.state != driver.STATE_STOPPED:
                    raise BadRequest('Start action requires all hosts to be '
                                     'in the stopped state first. At least '
                                     'one host is reporting an invalid state: '
                                     '{0}'.format(host.state))
                if action == driver.ACTION_STOP and \
                   host.state != driver.STATE_RUNNING:
                    raise BadRequest('Stop action requires all hosts to be in '
                                     'the running state first. At least one '
                                     'host is reporting an invalid state: '
                                     '{0}'.format(host.state))
                if action == driver.ACTION_TERMINATE and \
                   host.state not in (driver.STATE_RUNNING,
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
                "results_urls" : [] 
            }

            for id in action_ids:
                ret['results_urls'].append(reverse(
                    'stackaction-detail',
                    kwargs={
                        'pk': id,
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

        if action == BaseCloudProvider.ACTION_PROVISION:
            task_list.append(tasks.highstate.si(stack.id))
            task_list.append(tasks.orchestrate.si(stack.id))

        if action == BaseCloudProvider.ACTION_ORCHESTRATE:
            task_list.append(tasks.orchestrate.si(stack.id))

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
    model = models.StackAction
    serializer_class = serializers.StackActionSerializer

    def get_queryset(self):
        stack = self.get_object()
        return models.StackAction.objects.filter(stack=stack)


class StackActionDetailAPIView(generics.RetrieveDestroyAPIView):
    model = models.StackAction
    serializer_class = serializers.StackActionSerializer


@api_view(['GET'])
def stack_action_zip(request, pk):
    actions = models.StackAction.objects.filter(pk=pk)
    if len(actions) is 1:
        action = actions[0]

        if len(action.std_out()) is 0:
            return Response({"detail": "Not found"})

        buffer = StringIO.StringIO()
        action_zip = zipfile.ZipFile(buffer, 'w')

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

        response = HttpResponse(buffer.getvalue(),
                                content_type='application/zip')
        response['Content-Disposition'] = (
            'attachment; filename={0}.zip'.format(filename)
        )
        return response
    else:
        return Response({"detail": "Not found"})


class StackHistoryList(generics.ListAPIView):
    model = models.StackHistory
    serializer_class = serializers.StackHistorySerializer


class HostListAPIView(PublicStackMixin, generics.ListAPIView):
    model = models.Host
    serializer_class = serializers.HostSerializer
    parser_classes = (parsers.JSONParser,)

    def get_queryset(self):
        return models.Host.objects.filter(stack__owner=self.request.user)


class StackHostsAPIView(HostListAPIView):

    def get_queryset(self):
        stack = self.get_object()
        return models.Host.objects.filter(stack=stack)

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
                stack.hosts.filter(blueprint_host_definition=hostdef)
                .order_by('-index')[:count]
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
        provider_metadata = request \
            .QUERY_PARAMS \
            .get('provider_metadata') == 'true'
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


class StackVolumesAPIView(PublicStackMixin, VolumeListAPIView):
    def get_queryset(self):
        return Volume.objects.filter(stack__pk=self.kwargs.get('pk'))


class HostDetailAPIView(generics.RetrieveDestroyAPIView):
    model = models.Host
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


class StackFQDNListAPIView(PublicStackMixin, APIView):
    model = models.Stack

    def get(self, request, *args, **kwargs):
        stack = self.get_object()
        fqdns = [h.fqdn for h in stack.hosts.all()]
        return Response(fqdns)


class StackLogsAPIView(PublicStackMixin, APIView):
    model = models.Stack

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


class StackProvisioningErrorsAPIView(PublicStackMixin, APIView):
    model = models.Stack

    def get(self, request, *args, **kwargs):
        stack = self.get_object()
        err_file = join(stack.get_root_directory(), 'provisioning.err.latest')
        if not isfile(err_file):
            raise BadRequest('No error file found for this stack. Has '
                             'provisioning occurred yet?')

        with open(err_file) as f:
            err_yaml = yaml.safe_load(f)
        return Response(err_yaml)


class StackOrchestrationErrorsAPIView(PublicStackMixin, APIView):
    model = models.Stack

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
    model = models.Stack
    renderer_classes = (PlainTextRenderer,)

    # TODO: Code complexity ignored for now
    def get(self, request, *args, **kwargs):  # NOQA
        stack = self.get_object()
        log_file = self.kwargs.get('log', '')

        try:
            tail = int(request.QUERY_PARAMS.get('tail', 0))
        except:
            tail = None

        try:
            head = int(request.QUERY_PARAMS.get('head', 0))
        except:
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
    model = SecurityGroup
    serializer_class = serializers.StackSecurityGroupSerializer

    def get_queryset(self):
        stack = self.get_object()
        return stack.get_security_groups()
