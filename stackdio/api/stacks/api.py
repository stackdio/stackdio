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
from guardian.shortcuts import assign_perm
from rest_framework import generics, status
from rest_framework.filters import DjangoFilterBackend, DjangoObjectPermissionsFilter
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.serializers import ValidationError

from stackdio.core.exceptions import BadRequest
from stackdio.core.permissions import StackdioModelPermissions, StackdioObjectPermissions
from stackdio.core.renderers import PlainTextRenderer, ZipRenderer
from stackdio.core.viewsets import (
    StackdioModelUserPermissionsViewSet,
    StackdioModelGroupPermissionsViewSet,
    StackdioObjectUserPermissionsViewSet,
    StackdioObjectGroupPermissionsViewSet,
)
from stackdio.api.cloud.filters import SecurityGroupFilter
from stackdio.api.formulas.models import FormulaVersion
from stackdio.api.formulas.serializers import FormulaVersionSerializer
from stackdio.api.volumes.serializers import VolumeSerializer
from . import filters, mixins, models, permissions, serializers, utils, workflows

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
    renderer_classes = (ZipRenderer,)

    def check_object_permissions(self, request, obj):
        # Check the permissions on the stack instead of the host
        super(StackCommandZipAPIView, self).check_object_permissions(request, obj.stack)

    def get(self, request, *args, **kwargs):
        command = self.get_object()

        filename = 'command_output_' + command.submit_time.strftime('%Y%m%d_%H%M%S')

        file_buffer = StringIO.StringIO()
        with zipfile.ZipFile(file_buffer, 'w') as command_zip:
            # Write out all the contents
            command_zip.writestr(
                str('{0}/__command'.format(filename)),
                str(command.command)
            )

            for output in command.std_out:
                command_zip.writestr(
                    str('{0}/{1}.txt'.format(filename, output['host'])),
                    str(output['output'])
                )

        # Give browsers a reasonable filename to save this as
        headers = {
            'Content-Disposition': 'attachment; filename={0}.zip'.format(filename)
        }

        return Response(file_buffer.getvalue(), headers=headers)


class StackHostsAPIView(mixins.StackRelatedMixin, generics.ListCreateAPIView):
    """
    Lists all hosts for the associated stack.

    #### POST /api/stacks/<stack_id\>/hosts/
    Allows users to add or remove hosts from a running stack.

        {
            "action": "add",
            "host_definition": "<slug>",
            "count": <int>,
            "backfill": <bool>
        }

    OR

        {
            "action": "remove",
            "host_definition": "<slug>",
            "count": <int>
        }

    where:

    `action` (string) REQUIRED -- either add or remove

    `count` (int) REQUIRED -- how many additional hosts to add / remove

    `host_definition` (string) REQUIRED -- the id of a blueprint host
        definition that is part of the blueprint the stack was initially
        launched from

    `backfill` (bool) OPTIONAL, DEFAULT=false -- if true, the hostnames
        will be generated in a way to fill in any gaps in the existing
        hostnames of the stack. For example, if your stack has a host list
        [foo-1, foo-3, foo-4] and you ask for three additional hosts, the
        resulting set of hosts is [foo-1, foo-2, foo-3, foo4, foo-5, foo-6]
    """
    serializer_class = serializers.HostSerializer
    filter_class = filters.HostFilter

    def get_queryset(self):
        stack = self.get_stack()
        return stack.hosts.all()

    def get_serializer_context(self):
        """
        We need the stack during serializer validation - so we'll throw it in the context
        """
        context = super(StackHostsAPIView, self).get_serializer_context()
        context['stack'] = self.get_stack()
        return context


class HostDetailAPIView(generics.RetrieveDestroyAPIView):
    queryset = models.Host.objects.all()
    serializer_class = serializers.HostSerializer
    permission_classes = (permissions.StackParentObjectPermissions,)

    def check_object_permissions(self, request, obj):
        # Check the permissions on the stack instead of the host
        super(HostDetailAPIView, self).check_object_permissions(request, obj.stack)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        # Return the host while its deleting
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def perform_destroy(self, instance):
        stack = instance.stack

        if stack.status != models.Stack.FINISHED:
            err_msg = 'You may not delete hosts on this stack in its current state: {0}'
            raise ValidationError({
                'stack': [err_msg.format(stack.status)]
            })

        instance.set_status(models.Host.DELETING, 'Deleting host.')

        host_ids = [instance.id]

        # unregister DNS and destroy the host
        workflows.DestroyHostsWorkflow(stack, host_ids).execute()


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
