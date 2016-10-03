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

from __future__ import unicode_literals

from django.conf.urls import include, url

from stackdio.core import routers
from . import api

model_router = routers.SimpleBulkRouter()
model_router.register(r'users',
                      api.StackModelUserPermissionsViewSet,
                      'stack-model-user-permissions')
model_router.register(r'groups',
                      api.StackModelGroupPermissionsViewSet,
                      'stack-model-group-permissions')


object_router = routers.SimpleBulkRouter()
object_router.register(r'users',
                       api.StackObjectUserPermissionsViewSet,
                       'stack-object-user-permissions')
object_router.register(r'groups',
                       api.StackObjectGroupPermissionsViewSet,
                       'stack-object-group-permissions')


urlpatterns = (
    url(r'^$',
        api.StackListAPIView.as_view(),
        name='stack-list'),

    url(r'^permissions/',
        include(model_router.urls)),

    url(r'^(?P<pk>[0-9]+)/$',
        api.StackDetailAPIView.as_view(),
        name='stack-detail'),

    url(r'^(?P<pk>[0-9]+)/properties/$',
        api.StackPropertiesAPIView.as_view(),
        name='stack-properties'),

    url(r'^(?P<parent_pk>[0-9]+)/permissions/',
        include(object_router.urls)),

    url(r'^(?P<parent_pk>[0-9]+)/hosts/$',
        api.StackHostListAPIView.as_view(),
        name='stack-host-list'),

    url(r'^(?P<parent_pk>[0-9]+)/hosts/(?P<pk>[0-9]+)/$',
        api.StackHostDetailAPIView.as_view(),
        name='stack-host-detail'),

    url(r'^(?P<parent_pk>[0-9]+)/volumes/$',
        api.StackVolumeListAPIView.as_view(),
        name='stack-volume-list'),

    url(r'^(?P<parent_pk>[0-9]+)/labels/$',
        api.StackLabelListAPIView.as_view(),
        name='stack-label-list'),

    url(r'^(?P<parent_pk>[0-9]+)/labels/(?P<label_name>[\w.@+-]+)/$',
        api.StackLabelDetailAPIView.as_view(),
        name='stack-label-detail'),

    url(r'^(?P<parent_pk>[0-9]+)/user_channels/$',
        api.StackUserChannelsListAPIView.as_view(),
        name='stack-user-channel-list'),

    url(r'^(?P<parent_pk>[0-9]+)/group_channels/$',
        api.StackGroupChannelsListAPIView.as_view(),
        name='stack-group-channel-list'),

    url(r'^(?P<parent_pk>[0-9]+)/history/$',
        api.StackHistoryAPIView.as_view(),
        name='stack-history'),

    url(r'^(?P<parent_pk>[0-9]+)/logs/$',
        api.StackLogsAPIView.as_view(),
        name='stack-logs'),

    url(r'^(?P<parent_pk>[0-9]+)/logs/(?P<log>.*)$',
        api.StackLogsDetailAPIView.as_view(),
        name='stack-logs-detail'),

    url(r'^(?P<parent_pk>[0-9]+)/action/$',
        api.StackActionAPIView.as_view(),
        name='stack-action'),

    url(r'^(?P<parent_pk>[0-9]+)/commands/$',
        api.StackCommandListAPIView.as_view(),
        name='stack-command-list'),

    url(r'^(?P<parent_pk>[0-9]+)/commands/(?P<pk>[0-9]+)/$',
        api.StackCommandDetailAPIView.as_view(),
        name='stack-command-detail'),

    url(r'^(?P<parent_pk>[0-9]+)/commands/(?P<pk>[0-9]+)\.zip$',
        api.StackCommandZipAPIView.as_view(),
        name='stack-command-zip'),

    url(r'^(?P<parent_pk>[0-9]+)/security_groups/$',
        api.StackSecurityGroupsAPIView.as_view(),
        name='stack-security-groups'),

    url(r'^(?P<parent_pk>[0-9]+)/formula_versions/$',
        api.StackFormulaVersionsAPIView.as_view(),
        name='stack-formula-versions'),
)
