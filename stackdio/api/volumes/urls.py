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
                      api.VolumeModelUserPermissionsViewSet,
                      'volume-model-user-permissions')
model_router.register(r'groups',
                      api.VolumeModelGroupPermissionsViewSet,
                      'volume-model-group-permissions')


object_router = routers.SimpleBulkRouter()
object_router.register(r'users',
                       api.VolumeObjectUserPermissionsViewSet,
                       'volume-object-user-permissions')
object_router.register(r'groups',
                       api.VolumeObjectGroupPermissionsViewSet,
                       'volume-object-group-permissions')


urlpatterns = (
    url(r'^$',
        api.VolumeListAPIView.as_view(),
        name='volume-list'),

    url(r'^permissions/',
        include(model_router.urls)),

    url(r'^(?P<pk>[0-9]+)/$',
        api.VolumeDetailAPIView.as_view(),
        name='volume-detail'),

    url(r'^(?P<parent_pk>[0-9]+)/permissions/',
        include(object_router.urls)),
)
