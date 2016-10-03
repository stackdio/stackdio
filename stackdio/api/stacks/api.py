# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
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


import logging
import zipfile
from collections import OrderedDict
from os import listdir
from os.path import join, isfile

import envoy
from actstream import action
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import assign_perm
from rest_framework import generics, status
from rest_framework.filters import DjangoFilterBackend, DjangoObjectPermissionsFilter
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.serializers import ValidationError
from six import StringIO

from stackdio.api.cloud.filters import SecurityGroupFilter
from stackdio.api.formulas.models import FormulaVersion
from stackdio.api.formulas.serializers import FormulaVersionSerializer
from stackdio.api.volumes.serializers import VolumeSerializer
from stackdio.core.constants import Activity
from stackdio.core.notifications.serializers import (
    UserSubscriberNotificationChannelSerializer,
    GroupSubscriberNotificationChannelSerializer,
)
from stackdio.core.permissions import StackdioModelPermissions, StackdioObjectPermissions
from stackdio.core.renderers import PlainTextRenderer, ZipRenderer
from stackdio.core.viewsets import (
    StackdioModelUserPermissionsViewSet,
    StackdioModelGroupPermissionsViewSet,
    StackdioObjectUserPermissionsViewSet,
    StackdioObjectGroupPermissionsViewSet,
)
from . import filters, mixins, models, serializers, utils, workflows

logger = logging.getLogger(__name__)


class StackListAPIView(generics.ListCreateAPIView):
    """
    Displays a list of all stacks visible to you.
    """
    queryset = models.Stack.objects.all()
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

        stack.labels.create(key='owner', value=self.request.user.username)

        # Create all the formula versions from the blueprint
        for formula_version in stack.blueprint.formula_versions.all():
            # Make sure the version doesn't already exist (could have been created in
            # the serializer.save() call)
            try:
                stack.formula_versions.get(formula=formula_version.formula)
            except FormulaVersion.DoesNotExist:
                stack.formula_versions.create(formula=formula_version.formula,
                                              version=formula_version.version)


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

        # Check the activity
        if stack.activity not in Activity.can_delete:
            err_msg = ('You may not delete this stack in its current state.  Please wait until '
                       'it is finished with the current action.')
            raise ValidationError({
                'detail': [err_msg]
            })

        # Update the status
        stack.set_activity(Activity.QUEUED)
        action.send(self.request.user, verb='deleted', action_object=instance)

        # Execute the workflow to delete the infrastructure
        workflow = workflows.DestroyStackWorkflow(stack, opts=self.request.data)
        workflow.execute()


class StackPropertiesAPIView(generics.RetrieveUpdateAPIView):
    queryset = models.Stack.objects.all()
    serializer_class = serializers.StackPropertiesSerializer
    permission_classes = (StackdioObjectPermissions,)


class StackHistoryAPIView(mixins.StackRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.StackHistorySerializer

    def get_queryset(self):
        stack = self.get_stack()
        return stack.history.all()


class StackActionAPIView(mixins.StackRelatedMixin, generics.GenericAPIView):
    serializer_class = serializers.StackActionSerializer

    def get(self, request, *args, **kwargs):
        stack = self.get_stack()
        # Grab the list of available actions for the current stack activity
        available_actions = Activity.action_map.get(stack.activity, [])

        # Filter them based on permissions
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
        return stack.commands.all()

    def perform_create(self, serializer):
        serializer.save(stack=self.get_stack())


class StackCommandDetailAPIView(mixins.StackRelatedMixin, generics.RetrieveDestroyAPIView):
    serializer_class = serializers.StackCommandSerializer

    def get_queryset(self):
        stack = self.get_stack()
        return stack.commands.all()


class StackCommandZipAPIView(mixins.StackRelatedMixin, generics.GenericAPIView):
    renderer_classes = (ZipRenderer,)

    def get_queryset(self):
        stack = self.get_stack()
        return stack.commands.all()

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


class StackLabelListAPIView(mixins.StackRelatedMixin, generics.ListCreateAPIView):
    serializer_class = serializers.StackLabelSerializer

    def get_queryset(self):
        stack = self.get_stack()
        return stack.labels.all()

    def get_serializer_context(self):
        context = super(StackLabelListAPIView, self).get_serializer_context()
        context['content_object'] = self.get_stack()
        return context

    def perform_create(self, serializer):
        serializer.save(content_object=self.get_stack())


class StackLabelDetailAPIView(mixins.StackRelatedMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.StackLabelSerializer
    lookup_field = 'key'
    lookup_url_kwarg = 'label_name'

    def get_queryset(self):
        stack = self.get_stack()
        return stack.labels.all()

    def get_serializer_context(self):
        context = super(StackLabelDetailAPIView, self).get_serializer_context()
        context['content_object'] = self.get_stack()
        return context


class StackUserChannelsListAPIView(mixins.StackRelatedMixin, generics.ListCreateAPIView):
    serializer_class = UserSubscriberNotificationChannelSerializer

    def get_queryset(self):
        stack = self.get_stack()
        return stack.subscribed_channels.filter(auth_object=self.request.user)

    def get_serializer_context(self):
        context = super(StackUserChannelsListAPIView, self).get_serializer_context()
        context['auth_object'] = self.request.user
        return context

    def perform_create(self, serializer):
        serializer.save(auth_object=self.request.user, subscribed_object=self.get_stack())


class StackGroupChannelsListAPIView(mixins.StackRelatedMixin, generics.ListCreateAPIView):
    serializer_class = GroupSubscriberNotificationChannelSerializer

    def get_queryset(self):
        stack = self.get_stack()
        group_ctype = ContentType.objects.get_for_model(Group)
        # We want all the subscribed channels that are associated with groups
        return stack.subscribed_channels.filter(auth_object_content_type=group_ctype)

    def perform_create(self, serializer):
        serializer.save(subscribed_object=self.get_stack())


class StackHostListAPIView(mixins.StackRelatedMixin, generics.ListCreateAPIView):
    """
    Lists all hosts for the associated stack.

    #### POST /api/stacks/<stack_id>/hosts/
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
        context = super(StackHostListAPIView, self).get_serializer_context()
        context['stack'] = self.get_stack()
        return context


class StackHostDetailAPIView(mixins.StackRelatedMixin, generics.RetrieveDestroyAPIView):
    serializer_class = serializers.HostSerializer

    def get_queryset(self):
        stack = self.get_stack()
        return stack.hosts.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        # Return the host while its deleting
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def perform_destroy(self, instance):
        stack = instance.stack

        if stack.activity not in Activity.can_delete:
            err_msg = 'You may not delete hosts on this stack in its current state: {0}'
            raise ValidationError({
                'stack': [err_msg.format(stack.activity)]
            })

        instance.set_activity(Activity.QUEUED)
        action.send(self.request.user, verb='deleted', action_object=instance)

        host_ids = [instance.id]

        # unregister DNS and destroy the host
        workflows.DestroyHostsWorkflow(stack, host_ids).execute()


class StackVolumeListAPIView(mixins.StackRelatedMixin, generics.ListAPIView):
    serializer_class = VolumeSerializer

    def get_queryset(self):
        stack = self.get_stack()
        return stack.volumes.all()


class StackLogsAPIView(mixins.StackRelatedMixin, generics.GenericAPIView):

    log_types = (
        'launch',
        'provisioning',
        'provisioning-error',
        'global_orchestration',
        'global_orchestration-error',
        'orchestration',
        'orchestration-error',
    )

    def get(self, request, *args, **kwargs):
        stack = self.get_stack()
        root_dir = stack.get_root_directory()
        log_dir = stack.get_log_directory()

        latest = OrderedDict()

        for log_type in self.log_types:
            spl = log_type.split('-')
            if len(spl) > 1 and spl[1] == 'error':
                log_file = '%s.err.latest' % spl[0]
            else:
                log_file = '%s.log.latest' % log_type

            if isfile(join(root_dir, log_file)):
                latest[log_type] = reverse(
                    'api:stacks:stack-logs-detail',
                    kwargs={'parent_pk': stack.pk, 'log': log_file},
                    request=request,
                )

        historical = [
            reverse('api:stacks:stack-logs-detail',
                    kwargs={'parent_pk': stack.pk, 'log': log},
                    request=request)
            for log in sorted(listdir(log_dir))
        ]

        ret = OrderedDict((
            ('latest', latest),
            ('historical', historical),
        ))

        return Response(ret)


class StackLogsDetailAPIView(mixins.StackRelatedMixin, generics.GenericAPIView):
    renderer_classes = (PlainTextRenderer,)

    # TODO: Code complexity ignored for now
    def get(self, request, *args, **kwargs):  # NOQA
        stack = self.get_stack()
        log_file = self.kwargs.get('log', '')

        try:
            tail = int(request.query_params.get('tail', 0))
        except ValueError:
            tail = None

        try:
            head = int(request.query_params.get('head', 0))
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
            raise ValidationError({
                'log_file': ['Log file does not exist: {0}.'.format(log_file)]
            })

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

    def perform_create(self, serializer):
        serializer.save(content_object=self.get_stack())


class StackModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    model_cls = models.Stack


class StackModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    model_cls = models.Stack


class StackObjectUserPermissionsViewSet(mixins.StackPermissionsMixin,
                                        StackdioObjectUserPermissionsViewSet):
    pass


class StackObjectGroupPermissionsViewSet(mixins.StackPermissionsMixin,
                                         StackdioObjectGroupPermissionsViewSet):
    pass
