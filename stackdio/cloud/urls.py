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

providertype_object_router = routers.SimpleRouter()
providertype_object_router.register(r'users',
                                    api.CloudProviderTypeObjectUserPermissionsViewSet,
                                    'cloudprovidertype-object-user-permissions')
providertype_object_router.register(r'groups',
                                    api.CloudProviderTypeObjectGroupPermissionsViewSet,
                                    'cloudprovidertype-object-group-permissions')

provider_model_router = routers.SimpleRouter()
provider_model_router.register(r'users',
                               api.CloudProviderModelUserPermissionsViewSet,
                               'cloudprovider-model-user-permissions')
provider_model_router.register(r'groups',
                               api.CloudProviderModelGroupPermissionsViewSet,
                               'cloudprovider-model-group-permissions')

provider_object_router = routers.SimpleRouter()
provider_object_router.register(r'users',
                                api.CloudProviderObjectUserPermissionsViewSet,
                                'cloudprovider-object-user-permissions')
provider_object_router.register(r'groups',
                                api.CloudProviderObjectGroupPermissionsViewSet,
                                'cloudprovider-object-group-permissions')

profile_model_router = routers.SimpleRouter()
profile_model_router.register(r'users',
                              api.CloudProfileModelUserPermissionsViewSet,
                              'cloudprofile-model-user-permissions')
profile_model_router.register(r'groups',
                              api.CloudProfileModelGroupPermissionsViewSet,
                              'cloudprofile-model-group-permissions')

profile_object_router = routers.SimpleRouter()
profile_object_router.register(r'users',
                               api.CloudProfileObjectUserPermissionsViewSet,
                               'cloudprofile-object-user-permissions')
profile_object_router.register(r'groups',
                               api.CloudProfileObjectGroupPermissionsViewSet,
                               'cloudprofile-object-group-permissions')

snapshot_model_router = routers.SimpleRouter()
snapshot_model_router.register(r'users',
                               api.SnapshotModelUserPermissionsViewSet,
                               'snapshot-model-user-permissions')
snapshot_model_router.register(r'groups',
                               api.SnapshotModelGroupPermissionsViewSet,
                               'snapshot-model-group-permissions')

snapshot_object_router = routers.SimpleRouter()
snapshot_object_router.register(r'users',
                                api.SnapshotObjectUserPermissionsViewSet,
                                'snapshot-object-user-permissions')
snapshot_object_router.register(r'groups',
                                api.SnapshotObjectGroupPermissionsViewSet,
                                'snapshot-object-group-permissions')

urlpatterns = patterns(
    'cloud.api',

    url(r'^provider_types/$',
        api.CloudProviderTypeListAPIView.as_view(),
        name='cloudprovidertype-list'),

    url(r'^provider_types/(?P<type_name>[\w.@+-]+)/$',
        api.CloudProviderTypeDetailAPIView.as_view(),
        name='cloudprovidertype-detail'),

    url(r'^provider_types/(?P<type_name>[\w.@+-]+)/permissions/',
        include(providertype_object_router.urls)),

    url(r'^provider_types/(?P<type_name>[\w.@+-]+)/instance_sizes/$',
        api.CloudInstanceSizeListAPIView.as_view(),
        name='cloudinstancesize-list'),

    url(r'^provider_types/(?P<type_name>[\w.@+-]+)/instance_sizes/(?P<instance_id>[\w.@+-]+)/$',
        api.CloudInstanceSizeDetailAPIView.as_view(),
        name='cloudinstancesize-detail'),

    url(r'^provider_types/(?P<type_name>[\w.@+-]+)/regions/$',
        api.CloudRegionListAPIView.as_view(),
        name='cloudregion-list'),

    url(r'^provider_types/(?P<type_name>[\w.@+-]+)/regions/(?P<title>[\w.@+-]+)/$',
        api.CloudRegionDetailAPIView.as_view(),
        name='cloudregion-detail'),

    url(r'^provider_types/(?P<type_name>[\w.@+-]+)/regions/(?P<title>[\w.@+-]+)/zones/$',
        api.CloudRegionZoneListAPIView.as_view(),
        name='cloudregion-zones'),

    url(r'^provider_types/(?P<type_name>[\w.@+-]+)/zones/$',
        api.CloudZoneListAPIView.as_view(),
        name='cloudzone-list'),

    url(r'^provider_types/(?P<type_name>[\w.@+-]+)/zones/(?P<title>[\w.@+-]+)/$',
        api.CloudZoneDetailAPIView.as_view(),
        name='cloudzone-detail'),

    url(r'^providers/$',
        api.CloudProviderListAPIView.as_view(),
        name='cloudprovider-list'),

    url(r'^providers/permissions/',
        include(provider_model_router.urls)),

    url(r'^providers/(?P<pk>[0-9]+)/$',
        api.CloudProviderDetailAPIView.as_view(),
        name='cloudprovider-detail'),

    url(r'^providers/(?P<pk>[0-9]+)/security_groups/$',
        api.CloudProviderSecurityGroupListAPIView.as_view(),
        name='cloudprovider-securitygroup-list'),

    url(r'^providers/(?P<pk>[0-9]+)/vpc_subnets/$',
        api.CloudProviderVPCSubnetListAPIView.as_view(),
        name='cloudprovider-vpcsubnet-list'),

    url(r'^providers/(?P<pk>[0-9]+)/global_orchestration_components/$',
        api.GlobalOrchestrationComponentListAPIView.as_view(),
        name='cloudprovider-global-orchestration-list'),

    url(r'^providers/(?P<pk>[0-9]+)/global_orchestration_properties/$',
        api.GlobalOrchestrationPropertiesAPIView.as_view(),
        name='cloudprovider-global-orchestration-properties'),

    url(r'^providers/(?P<pk>[0-9]+)/formula_versions/$',
        api.CloudProviderFormulaVersionsAPIView.as_view(),
        name='cloudprovider-formula-versions'),

    url(r'^providers/(?P<pk>[0-9]+)/permissions/',
        include(provider_object_router.urls)),

    url(r'^global_orchestration_components/(?P<pk>[0-9]+)/$',
        api.GlobalOrchestrationComponentDetailAPIView.as_view(),
        name='globalorchestrationformulacomponent-detail'),

    url(r'^profiles/$',
        api.CloudProfileListAPIView.as_view(),
        name='cloudprofile-list'),

    url(r'^profiles/permissions/',
        include(profile_model_router.urls)),

    url(r'^profiles/(?P<pk>[0-9]+)/$',
        api.CloudProfileDetailAPIView.as_view(),
        name='cloudprofile-detail'),

    url(r'^profiles/(?P<pk>[0-9]+)/permissions/',
        include(profile_object_router.urls)),

    url(r'^snapshots/$',
        api.SnapshotListAPIView.as_view(),
        name='snapshot-list'),

    url(r'^snapshots/permissions/',
        include(snapshot_model_router.urls)),

    url(r'^snapshots/(?P<pk>[0-9]+)/$',
        api.SnapshotDetailAPIView.as_view(),
        name='snapshot-detail'),

    url(r'^snapshots/(?P<pk>[0-9]+)/permissions/',
        include(snapshot_object_router.urls)),

    url(r'^security_groups/$',
        api.SecurityGroupListAPIView.as_view(),
        name='securitygroup-list'),

    url(r'^security_groups/(?P<pk>[0-9]+)/$',
        api.SecurityGroupDetailAPIView.as_view(),
        name='securitygroup-detail'),

    url(r'^security_groups/(?P<pk>[0-9]+)/rules/$',
        api.SecurityGroupRulesAPIView.as_view(),
        name='securitygroup-rules'),
)
