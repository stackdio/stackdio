# -*- coding: utf-8 -*-

# Copyright 2017,  Digital Reasoning
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
from stackdio.api.environments import api
from stackdio.core import routers

model_router = routers.SimpleBulkRouter()
model_router.register(r'users',
                      api.EnvironmentModelUserPermissionsViewSet,
                      'environment-model-user-permissions')
model_router.register(r'groups',
                      api.EnvironmentModelGroupPermissionsViewSet,
                      'environment-model-group-permissions')


object_router = routers.SimpleBulkRouter()
object_router.register(r'users',
                       api.EnvironmentObjectUserPermissionsViewSet,
                       'environment-object-user-permissions')
object_router.register(r'groups',
                       api.EnvironmentObjectGroupPermissionsViewSet,
                       'environment-object-group-permissions')


urlpatterns = (
    url(r'^$',
        api.EnvironmentListAPIView.as_view(),
        name='environment-list'),

    url(r'^permissions/',
        include(model_router.urls)),

    url(r'^(?P<name>[a-z0-9\-_]+)/$',
        api.EnvironmentDetailAPIView.as_view(),
        name='environment-detail'),

    url(r'^(?P<name>[a-z0-9\-_]+)/properties/$',
        api.EnvironmentPropertiesAPIView.as_view(),
        name='environment-properties'),

    url(r'^(?P<parent_name>[a-z0-9\-_]+)/permissions/',
        include(object_router.urls)),

    url(r'^(?P<parent_name>[a-z0-9\-_]+)/components/$',
        api.EnvironmentComponentListAPIView.as_view(),
        name='environment-component-list'),

    url(r'^(?P<parent_name>[a-z0-9\-_]+)/labels/$',
        api.EnvironmentLabelListAPIView.as_view(),
        name='environment-label-list'),

    url(r'^(?P<parent_name>[a-z0-9\-_]+)/labels/(?P<label_name>[\w.@+-]+)/$',
        api.EnvironmentLabelDetailAPIView.as_view(),
        name='environment-label-detail'),

    url(r'^(?P<parent_name>[a-z0-9\-_]+)/hosts/$',
        api.EnvironmentHostListAPIView.as_view(),
        name='environment-host-list'),

    url(r'^(?P<parent_name>[a-z0-9\-_]+)/action/$',
        api.EnvironmentActionAPIView.as_view(),
        name='environment-action'),

    url(r'^(?P<parent_name>[a-z0-9\-_]+)/formula_versions/$',
        api.EnvironmentFormulaVersionsAPIView.as_view(),
        name='environment-formula-versions'),

    url(r'^(?P<parent_name>[a-z0-9\-_]+)/logs/$',
        api.EnvironmentLogsAPIView.as_view(),
        name='environment-logs'),

    url(r'^(?P<parent_name>[a-z0-9\-_]+)/logs/(?P<log>.*)$',
        api.EnvironmentLogsDetailAPIView.as_view(),
        name='environment-logs-detail'),
)
