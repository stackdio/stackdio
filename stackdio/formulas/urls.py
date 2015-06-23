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
                      api.FormulaModelUserPermissionsViewSet,
                      'formula-model-user-permissions')
model_router.register(r'groups',
                      api.FormulaModelGroupPermissionsViewSet,
                      'formula-model-group-permissions')


object_router = routers.SimpleRouter()
object_router.register(r'users',
                       api.FormulaObjectUserPermissionsViewSet,
                       'formula-object-user-permissions')
object_router.register(r'groups',
                       api.FormulaObjectGroupPermissionsViewSet,
                       'formula-object-group-permissions')


urlpatterns = patterns(
    'formulas.api',

    url(r'^formulas/$',
        api.FormulaListAPIView.as_view(),
        name='formula-list'),

    url(r'^formulas/permissions/',
        include(model_router.urls)),

    url(r'^formulas/(?P<pk>[0-9]+)/$',
        api.FormulaDetailAPIView.as_view(),
        name='formula-detail'),

    # Pull the default pillar/properties defined in the SPECFILE
    url(r'^formulas/(?P<pk>[0-9]+)/properties/$',
        api.FormulaPropertiesAPIView.as_view(),
        name='formula-properties'),

    url(r'^formulas/(?P<pk>[0-9]+)/action/$',
        api.FormulaActionAPIView.as_view(),
        name='formula-action'),

    url(r'^formulas/(?P<pk>[0-9]+)/permissions/',
        include(object_router.urls)),

    url(r'^formula_components/(?P<pk>[0-9]+)/$',
        api.FormulaComponentDetailAPIView.as_view(),
        name='formulacomponent-detail'),
)
