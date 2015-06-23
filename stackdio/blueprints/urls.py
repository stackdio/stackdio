# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
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


from django.conf.urls import include, patterns, url
from rest_framework import routers

from . import api

model_router = routers.SimpleRouter()
model_router.register(r'users',
                      api.BlueprintModelUserPermissionsViewSet,
                      'blueprint-model-user-permissions')
model_router.register(r'groups',
                      api.BlueprintModelGroupPermissionsViewSet,
                      'blueprint-model-group-permissions')


object_router = routers.SimpleRouter()
object_router.register(r'users',
                       api.BlueprintObjectUserPermissionsViewSet,
                       'blueprint-object-user-permissions')
object_router.register(r'groups',
                       api.BlueprintObjectGroupPermissionsViewSet,
                       'blueprint-object-group-permissions')


urlpatterns = patterns(
    'blueprints.api',

    url(r'^blueprints/$',
        api.BlueprintListAPIView.as_view(),
        name='blueprint-list'),

    url(r'^blueprints/permissions/',
        include(model_router.urls)),

    url(r'^blueprints/(?P<pk>[0-9]+)/$',
        api.BlueprintDetailAPIView.as_view(),
        name='blueprint-detail'),

    url(r'^blueprints/(?P<pk>[0-9]+)/properties/$',
        api.BlueprintPropertiesAPIView.as_view(),
        name='blueprint-properties'),

    url(r'^blueprints/(?P<pk>[0-9]+)/permissions/',
        include(object_router.urls)),

    url(r'^blueprints/(?P<pk>[0-9]+)/formula_versions/$',
        api.BlueprintFormulaVersionsAPIView.as_view(),
        name='blueprint-formula-versions'),
)
