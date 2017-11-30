# -*- coding: utf-8 -*-

# Copyright 2017,  Digital Reasoning
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

from __future__ import absolute_import, unicode_literals

import logging
import os
from collections import OrderedDict

import envoy
from guardian.shortcuts import assign_perm
from rest_framework import generics, status
from rest_framework.filters import DjangoFilterBackend, DjangoObjectPermissionsFilter
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.serializers import ValidationError
from stackdio.api.environments import filters, mixins, models, serializers, utils
from stackdio.api.formulas.serializers import FormulaVersionSerializer
from stackdio.core.constants import Activity
from stackdio.core.permissions import StackdioModelPermissions, StackdioObjectPermissions
from stackdio.core.renderers import PlainTextRenderer
from stackdio.core.serializers import ObjectPropertiesSerializer
from stackdio.core.viewsets import (
    StackdioModelUserPermissionsViewSet,
    StackdioModelGroupPermissionsViewSet,
    StackdioObjectUserPermissionsViewSet,
    StackdioObjectGroupPermissionsViewSet,
)

logger = logging.getLogger(__name__)


class EnvironmentListAPIView(generics.ListCreateAPIView):
    """
    Displays a list of all environments visible to you.
    """
    queryset = models.Environment.objects.all()
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.EnvironmentFilter
    lookup_field = 'name'

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.FullEnvironmentSerializer
        else:
            return serializers.EnvironmentSerializer

    def perform_create(self, serializer):
        env = serializer.save()
        for perm in models.Environment.object_permissions:
            assign_perm('environments.%s_environment' % perm, self.request.user, env)


class EnvironmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Environment.objects.all()
    serializer_class = serializers.EnvironmentSerializer
    permission_classes = (StackdioObjectPermissions,)
    lookup_field = 'name'


class EnvironmentPropertiesAPIView(generics.RetrieveUpdateAPIView):
    queryset = models.Environment.objects.all()
    serializer_class = ObjectPropertiesSerializer
    permission_classes = (StackdioObjectPermissions,)
    lookup_field = 'name'


class EnvironmentHostListAPIView(mixins.EnvironmentRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.EnvironmentHostSerializer

    def get_queryset(self):
        environment = self.get_environment()
        return sorted(environment.get_current_hosts(), key=lambda x: x['id'])


class EnvironmentLabelListAPIView(mixins.EnvironmentRelatedMixin, generics.ListCreateAPIView):
    serializer_class = serializers.EnvironmentLabelSerializer

    def get_queryset(self):
        environment = self.get_environment()
        return environment.labels.all()

    def get_serializer_context(self):
        context = super(EnvironmentLabelListAPIView, self).get_serializer_context()
        context['content_object'] = self.get_environment()
        return context

    def perform_create(self, serializer):
        serializer.save(content_object=self.get_environment())


class EnvironmentLabelDetailAPIView(mixins.EnvironmentRelatedMixin,
                                    generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.EnvironmentLabelSerializer
    lookup_field = 'key'
    lookup_url_kwarg = 'label_name'

    def get_queryset(self):
        environment = self.get_environment()
        return environment.labels.all()

    def get_serializer_context(self):
        context = super(EnvironmentLabelDetailAPIView, self).get_serializer_context()
        context['content_object'] = self.get_environment()
        return context


class EnvironmentComponentListAPIView(mixins.EnvironmentRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.EnvironmentComponentSerializer

    def get_queryset(self):
        environment = self.get_environment()
        return environment.get_components()


class EnvironmentActionAPIView(mixins.EnvironmentRelatedMixin, generics.GenericAPIView):
    serializer_class = serializers.EnvironmentActionSerializer

    def get(self, request, *args, **kwargs):
        environment = self.get_environment()
        # Grab the list of available actions for the current environment activity
        available_actions = Activity.env_action_map.get(environment.activity, [])

        # Filter them based on permissions
        available_actions = utils.filter_actions(request.user, environment, available_actions)

        return Response({
            'available_actions': sorted(available_actions),
        })

    def post(self, request, *args, **kwargs):
        """
        POST request allows RPC-like actions to be called to interact
        with the environment. Request contains JSON with an `action` parameter
        and optional `args` depending on the action being executed.
        """
        environment = self.get_environment()

        serializer = self.get_serializer(environment, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class EnvironmentFormulaVersionsAPIView(mixins.EnvironmentRelatedMixin, generics.ListCreateAPIView):
    serializer_class = FormulaVersionSerializer

    def get_queryset(self):
        environment = self.get_environment()
        return environment.formula_versions.all()

    def perform_create(self, serializer):
        serializer.save(content_object=self.get_environment())


class EnvironmentLogsAPIView(mixins.EnvironmentRelatedMixin, generics.GenericAPIView):

    log_types = (
        'provisioning',
        'provisioning-error',
        'orchestration',
        'orchestration-error',
    )

    def get(self, request, *args, **kwargs):
        environment = self.get_environment()
        root_dir = environment.get_root_directory()
        log_dir = environment.get_log_directory()

        latest = OrderedDict()

        for log_type in self.log_types:
            spl = log_type.split('-')
            if len(spl) > 1 and spl[1] == 'error':
                log_file = '%s.err.latest' % spl[0]
            else:
                log_file = '%s.log.latest' % log_type

            if os.path.isfile(os.path.join(root_dir, log_file)):
                latest[log_type] = reverse(
                    'api:environments:environment-logs-detail',
                    kwargs={'parent_name': environment.name, 'log': log_file},
                    request=request,
                )

        historical = [
            reverse('api:environments:environment-logs-detail',
                    kwargs={'parent_name': environment.name, 'log': log},
                    request=request)
            for log in sorted(os.listdir(log_dir))
        ]

        ret = OrderedDict((
            ('latest', latest),
            ('historical', historical),
        ))

        return Response(ret)


class EnvironmentLogsDetailAPIView(mixins.EnvironmentRelatedMixin, generics.GenericAPIView):
    renderer_classes = (PlainTextRenderer,)

    # TODO: Code complexity ignored for now
    def get(self, request, *args, **kwargs):  # NOQA
        environment = self.get_environment()
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
            log = os.path.join(environment.get_root_directory(), log_file)
        elif log_file.endswith('.log') or log_file.endswith('.err'):
            log = os.path.join(environment.get_log_directory(), log_file)
        else:
            log = None

        if not log or not os.path.isfile(log):
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


class EnvironmentModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    model_cls = models.Environment


class EnvironmentModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    model_cls = models.Environment


class EnvironmentObjectUserPermissionsViewSet(mixins.EnvironmentPermissionsMixin,
                                              StackdioObjectUserPermissionsViewSet):
    pass


class EnvironmentObjectGroupPermissionsViewSet(mixins.EnvironmentPermissionsMixin,
                                               StackdioObjectGroupPermissionsViewSet):
    pass
