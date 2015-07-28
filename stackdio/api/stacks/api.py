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
from os import listdir
from os.path import join, isfile

import envoy
import yaml
from django.http import HttpResponse
from guardian.shortcuts import assign_perm
from rest_framework import generics, status, views
from rest_framework.decorators import api_view
from rest_framework.filters import DjangoFilterBackend, DjangoObjectPermissionsFilter
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.serializers import ValidationError

from stackdio.core.exceptions import BadRequest
from stackdio.core.permissions import StackdioModelPermissions, StackdioObjectPermissions
from stackdio.core.renderers import PlainTextRenderer
from stackdio.core.viewsets import (
    StackdioModelUserPermissionsViewSet,
    StackdioModelGroupPermissionsViewSet,
    StackdioObjectUserPermissionsViewSet,
    StackdioObjectGroupPermissionsViewSet,
)
from stackdio.api.blueprints.models import BlueprintHostDefinition
from stackdio.api.cloud.filters import SecurityGroupFilter
from stackdio.api.formulas.models import FormulaVersion
from stackdio.api.formulas.serializers import FormulaVersionSerializer
from stackdio.api.volumes.serializers import VolumeSerializer
from . import filters, mixins, models, permissions, serializers, utils, validators, workflows

logger = logging.getLogger(__name__)


class StackListAPIView(generics.ListCreateAPIView):
    """
    Displays a list of all stacks visible to you.
    """
    queryset = models.Stack.objects.all()
    serializer_class = serializers.StackSerializer
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.StackFilter

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.FullStackSerializer
        else:
            return serializers.StackSerializer

    def perform_create(self, serializer):
        stack = serializer.save()
        for perm in models.Stack.object_permissions:
            assign_perm('stacks.%s_stack' % perm, self.request.user, stack)


class StackDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Stack.objects.all()
    serializer_class = serializers.StackSerializer
    permission_classes = (StackdioObjectPermissions,)

    def destroy(self, request, *args, **kwargs):
        """
        Overriding the delete method to make sure the stack
        is taken offline before being deleted.  The default delete method
        returns a 204 status and we want to return a 202 with the serialized
        object
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def perform_destroy(self, instance):
        stack = instance

        # Check the status
        if stack.status not in models.Stack.SAFE_STATES:
            err_msg = ('You may not delete this stack in its current state.  Please wait until '
                       'it is finished with the current action.')
            raise ValidationError({
                'detail': err_msg
            })

        # Update the status
        msg = 'Stack will be removed upon successful termination of all machines'
        stack.set_status(models.Stack.DESTROYING,
                         models.Stack.DESTROYING, msg)

        # Execute the workflow to delete the infrastructure
        workflow = workflows.DestroyStackWorkflow(stack, opts=self.request.data)
        workflow.execute()


class StackModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    permission_classes = (permissions.StackPermissionsModelPermissions,)
    model_cls = models.Stack


class StackModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    permission_classes = (permissions.StackPermissionsModelPermissions,)
    model_cls = models.Stack


class StackPropertiesAPIView(mixins.StackRelatedMixin, generics.RetrieveUpdateAPIView):
    queryset = models.Stack.objects.all()
    serializer_class = serializers.StackPropertiesSerializer


class StackObjectUserPermissionsViewSet(mixins.StackRelatedMixin,
                                        StackdioObjectUserPermissionsViewSet):
    permission_classes = (permissions.StackPermissionsObjectPermissions,)


class StackObjectGroupPermissionsViewSet(mixins.StackRelatedMixin,
                                         StackdioObjectGroupPermissionsViewSet):
    permission_classes = (permissions.StackPermissionsObjectPermissions,)


class StackHistoryAPIView(mixins.StackRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.StackHistorySerializer

    def get_queryset(self):
        stack = self.get_stack()
        return stack.history.all()


class StackActionAPIView(mixins.StackRelatedMixin, generics.GenericAPIView):
    serializer_class = serializers.StackActionSerializer
    permission_classes = (permissions.StackActionObjectPermissions,)

    def get(self, request, *args, **kwargs):
        stack = self.get_stack()
        driver_hosts_map = stack.get_driver_hosts_map()
        available_actions = set()
        for driver, hosts in driver_hosts_map.iteritems():
            available_actions.update(driver.get_available_actions())

        available_actions = utils.filter_actions(request.user, stack, available_actions)

        return Response({
            'available_actions': sorted(available_actions),
        })

    def post(self, request, *args, **kwargs):
        """
        POST request allows RPC-like actions to be called to interact
        with the stack. Request contains JSON with an `action` parameter
        and optional `args` depending on the action being executed.
        """
        stack = self.get_stack()

        serializer = self.get_serializer(stack, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class StackCommandListAPIView(mixins.StackRelatedMixin, generics.ListCreateAPIView):
    serializer_class = serializers.StackCommandSerializer

    def get_queryset(self):
        stack = self.get_stack()
        return models.StackCommand.objects.filter(stack=stack)

    def perform_create(self, serializer):
        serializer.save(stack=self.get_stack())


class StackCommandDetailAPIView(generics.RetrieveDestroyAPIView):
    queryset = models.StackCommand.objects.all()
    serializer_class = serializers.StackCommandSerializer
    permission_classes = (permissions.StackParentObjectPermissions,)

    def check_object_permissions(self, request, obj):
        # Check the permissions on the stack instead of the host
        super(StackCommandDetailAPIView, self).check_object_permissions(request, obj.stack)


class StackCommandZipAPIView(generics.GenericAPIView):
    queryset = models.StackCommand.objects.all()
    permission_classes = (permissions.StackParentObjectPermissions,)

    def check_object_permissions(self, request, obj):
        # Check the permissions on the stack instead of the host
        super(StackCommandZipAPIView, self).check_object_permissions(request, obj.stack)

    def get(self, request, *args, **kwargs):
        command = self.get_object()

        file_buffer = StringIO.StringIO()
        action_zip = zipfile.ZipFile(file_buffer, 'w')

        filename = 'command_output_' + command.submit_time.strftime('%Y%m%d_%H%M%S')

        action_zip.writestr(
            str('{0}/__command'.format(filename)),
            str(command.command)
        )

        for output in command.std_out:
            action_zip.writestr(
                str('{0}/{1}.txt'.format(filename, output['host'])),
                str(output['output'])
            )

        action_zip.close()

        # The rest_framework Response object tries to render the data you give it.  We don't
        # want that, since this zip file we just generated is already 'rendered'.
        response = HttpResponse(file_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename={0}.zip'.format(filename)

        return response


class StackHostsAPIView(mixins.StackRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.HostSerializer

    def get_queryset(self):
        stack = self.get_stack()
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
        stack = self.get_stack()
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
            stack.generate_map_file()
            workflows.LaunchWorkflow(stack, host_ids=host_ids).execute()

        serializer = self.get_serializer(created_hosts, many=True)
        return Response(serializer.data)

    def remove_hosts(self, request):
        stack = self.get_stack()
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

        stack = self.get_stack()
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


class HostDetailAPIView(generics.RetrieveDestroyAPIView):
    queryset = models.Host.objects.all()
    serializer_class = serializers.HostSerializer
    permission_classes = (permissions.StackParentObjectPermissions,)

    def check_object_permissions(self, request, obj):
        # Check the permissions on the stack instead of the host
        super(HostDetailAPIView, self).check_object_permissions(request, obj.stack)

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


class StackVolumesAPIView(mixins.StackRelatedMixin, generics.ListAPIView):
    serializer_class = VolumeSerializer

    def get_queryset(self):
        stack = self.get_stack()
        return stack.volumes.all()


class StackFQDNListAPIView(mixins.StackRelatedMixin, generics.GenericAPIView):

    def get(self, request, *args, **kwargs):
        stack = self.get_stack()
        fqdns = [h.fqdn for h in stack.hosts.all()]
        return Response(fqdns)


class StackLogsAPIView(mixins.StackRelatedMixin, generics.GenericAPIView):

    def get(self, request, *args, **kwargs):
        stack = self.get_stack()
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


class StackProvisioningErrorsAPIView(mixins.StackRelatedMixin, generics.GenericAPIView):

    def get(self, request, *args, **kwargs):
        stack = self.get_stack()
        err_file = join(stack.get_root_directory(), 'provisioning.err.latest')
        if not isfile(err_file):
            raise BadRequest('No error file found for this stack. Has '
                             'provisioning occurred yet?')

        with open(err_file) as f:
            err_yaml = yaml.safe_load(f)
        return Response(err_yaml)


class StackOrchestrationErrorsAPIView(mixins.StackRelatedMixin, generics.GenericAPIView):

    def get(self, request, *args, **kwargs):
        stack = self.get_stack()
        err_file = join(stack.get_root_directory(), 'orchestration.err.latest')
        if not isfile(err_file):
            raise BadRequest('No error file found for this stack. Has '
                             'orchestration occurred yet?')

        with open(err_file) as f:
            err_yaml = yaml.safe_load(f)
        return Response(err_yaml)


class StackLogsDetailAPIView(StackLogsAPIView):
    renderer_classes = (PlainTextRenderer,)

    # TODO: Code complexity ignored for now
    def get(self, request, *args, **kwargs):  # NOQA
        stack = self.get_stack()
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


class StackSecurityGroupsAPIView(mixins.StackRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.StackSecurityGroupSerializer
    filter_class = SecurityGroupFilter

    def get_queryset(self):
        stack = self.get_stack()
        return stack.get_security_groups()


class StackFormulaVersionsAPIView(mixins.StackRelatedMixin, generics.ListCreateAPIView):
    serializer_class = FormulaVersionSerializer

    def get_queryset(self):
        stack = self.get_stack()
        return stack.formula_versions.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        formula = serializer.validated_data.get('formula')
        stack = self.get_stack()

        try:
            # Setting self.instance will cause self.update() to be called instead of
            # self.create() during save()
            serializer.instance = stack.formula_versions.get(formula=formula)
            response_code = status.HTTP_200_OK
        except FormulaVersion.DoesNotExist:
            # Return the proper response code
            response_code = status.HTTP_201_CREATED

        serializer.save(content_object=stack)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=response_code, headers=headers)
