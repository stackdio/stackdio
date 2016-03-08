# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from django.conf.urls import include, url
from rest_framework import routers

from . import api

model_router = routers.SimpleRouter()
model_router.register(r'users',
                      api.StackModelUserPermissionsViewSet,
                      'stack-model-user-permissions')
model_router.register(r'groups',
                      api.StackModelGroupPermissionsViewSet,
                      'stack-model-group-permissions')


object_router = routers.SimpleRouter()
object_router.register(r'users',
                       api.StackObjectUserPermissionsViewSet,
                       'stack-object-user-permissions')
object_router.register(r'groups',
                       api.StackObjectGroupPermissionsViewSet,
                       'stack-object-group-permissions')


urlpatterns = (
    url(r'^hosts/(?P<pk>[0-9]+)/$',
        api.HostDetailAPIView.as_view(),
        name='host-detail'),

    url(r'^commands/(?P<pk>[0-9]+)/$',
        api.StackCommandDetailAPIView.as_view(),
        name='stackcommand-detail'),

    url(r'^commands/(?P<pk>[0-9]+)\.zip$',
        api.StackCommandZipAPIView.as_view(),
        name='stackcommand-zip'),

    url(r'^stacks/$',
        api.StackListAPIView.as_view(),
        name='stack-list'),

    url(r'^stacks/permissions/',
        include(model_router.urls)),

    url(r'^stacks/(?P<pk>[0-9]+)/$',
        api.StackDetailAPIView.as_view(),
        name='stack-detail'),

    url(r'^stacks/(?P<pk>[0-9]+)/permissions/',
        include(object_router.urls)),

    url(r'^stacks/(?P<pk>[0-9]+)/hosts/$',
        api.StackHostsAPIView.as_view(),
        name='stack-hosts'),

    url(r'^stacks/(?P<pk>[0-9]+)/volumes/$',
        api.StackVolumesAPIView.as_view(),
        name='stack-volumes'),

    url(r'^stacks/(?P<pk>[0-9]+)/properties/$',
        api.StackPropertiesAPIView.as_view(),
        name='stack-properties'),

    url(r'^stacks/(?P<pk>[0-9]+)/labels/$',
        api.StackLabelListAPIView.as_view(),
        name='stack-label-list'),

    url(r'^stacks/(?P<pk>[0-9]+)/labels/(?P<label_name>[\w.@+-]+)/$',
        api.StackLabelDetailAPIView.as_view(),
        name='stack-label-detail'),

    url(r'^stacks/(?P<pk>[0-9]+)/history/$',
        api.StackHistoryAPIView.as_view(),
        name='stack-history'),

    url(r'^stacks/(?P<pk>[0-9]+)/logs/$',
        api.StackLogsAPIView.as_view(),
        name='stack-logs'),

    url(r'^stacks/(?P<pk>[0-9]+)/logs/(?P<log>.*)$',
        api.StackLogsDetailAPIView.as_view(),
        name='stack-logs-detail'),

    url(r'^stacks/(?P<pk>[0-9]+)/action/$',
        api.StackActionAPIView.as_view(),
        name='stack-action'),

    url(r'^stacks/(?P<pk>[0-9]+)/commands/$',
        api.StackCommandListAPIView.as_view(),
        name='stack-command-list'),

    url(r'^stacks/(?P<pk>[0-9]+)/security_groups/$',
        api.StackSecurityGroupsAPIView.as_view(),
        name='stack-security-groups'),

    url(r'^stacks/(?P<pk>[0-9]+)/formula_versions/$',
        api.StackFormulaVersionsAPIView.as_view(),
        name='stack-formula-versions'),
)
