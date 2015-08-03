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

provider_object_router = routers.SimpleRouter()
provider_object_router.register(r'users',
                                api.CloudProviderObjectUserPermissionsViewSet,
                                'cloudprovider-object-user-permissions')
provider_object_router.register(r'groups',
                                api.CloudProviderObjectGroupPermissionsViewSet,
                                'cloudprovider-object-group-permissions')

account_model_router = routers.SimpleRouter()
account_model_router.register(r'users',
                              api.CloudAccountModelUserPermissionsViewSet,
                              'cloudaccount-model-user-permissions')
account_model_router.register(r'groups',
                              api.CloudAccountModelGroupPermissionsViewSet,
                              'cloudaccount-model-group-permissions')

account_object_router = routers.SimpleRouter()
account_object_router.register(r'users',
                               api.CloudAccountObjectUserPermissionsViewSet,
                               'cloudaccount-object-user-permissions')
account_object_router.register(r'groups',
                               api.CloudAccountObjectGroupPermissionsViewSet,
                               'cloudaccount-object-group-permissions')

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

urlpatterns = (
    url(r'^$',
        api.CloudRootView.as_view(),
        name='cloud-root'),

    url(r'^providers/$',
        api.CloudProviderListAPIView.as_view(),
        name='cloudprovider-list'),

    url(r'^providers/(?P<name>[\w.@+-]+)/$',
        api.CloudProviderDetailAPIView.as_view(),
        name='cloudprovider-detail'),

    url(r'^providers/(?P<name>[\w.@+-]+)/permissions/',
        include(provider_object_router.urls)),

    url(r'^providers/(?P<name>[\w.@+-]+)/instance_sizes/$',
        api.CloudInstanceSizeListAPIView.as_view(),
        name='cloudinstancesize-list'),

    url(r'^providers/(?P<name>[\w.@+-]+)/instance_sizes/(?P<instance_id>[\w.@+-]+)/$',
        api.CloudInstanceSizeDetailAPIView.as_view(),
        name='cloudinstancesize-detail'),

    url(r'^providers/(?P<name>[\w.@+-]+)/regions/$',
        api.CloudRegionListAPIView.as_view(),
        name='cloudregion-list'),

    url(r'^providers/(?P<name>[\w.@+-]+)/regions/(?P<title>[\w.@+-]+)/$',
        api.CloudRegionDetailAPIView.as_view(),
        name='cloudregion-detail'),

    url(r'^providers/(?P<name>[\w.@+-]+)/regions/(?P<title>[\w.@+-]+)/zones/$',
        api.CloudRegionZoneListAPIView.as_view(),
        name='cloudregion-zones'),

    url(r'^providers/(?P<name>[\w.@+-]+)/zones/$',
        api.CloudZoneListAPIView.as_view(),
        name='cloudzone-list'),

    url(r'^providers/(?P<name>[\w.@+-]+)/zones/(?P<title>[\w.@+-]+)/$',
        api.CloudZoneDetailAPIView.as_view(),
        name='cloudzone-detail'),

    url(r'^accounts/$',
        api.CloudAccountListAPIView.as_view(),
        name='cloudaccount-list'),

    url(r'^accounts/permissions/',
        include(account_model_router.urls)),

    url(r'^accounts/(?P<pk>[0-9]+)/$',
        api.CloudAccountDetailAPIView.as_view(),
        name='cloudaccount-detail'),

    url(r'^accounts/(?P<pk>[0-9]+)/security_groups/$',
        api.CloudAccountSecurityGroupListAPIView.as_view(),
        name='cloudaccount-securitygroup-list'),

    url(r'^accounts/(?P<pk>[0-9]+)/security_groups/all/$',
        api.FullCloudAccountSecurityGroupListAPIView.as_view(),
        name='cloudaccount-fullsecuritygroup-list'),

    url(r'^accounts/(?P<pk>[0-9]+)/vpc_subnets/$',
        api.CloudAccountVPCSubnetListAPIView.as_view(),
        name='cloudaccount-vpcsubnet-list'),

    url(r'^accounts/(?P<pk>[0-9]+)/global_orchestration_components/$',
        api.GlobalOrchestrationComponentListAPIView.as_view(),
        name='cloudaccount-global-orchestration-list'),

    url(r'^accounts/(?P<pk>[0-9]+)/global_orchestration_properties/$',
        api.GlobalOrchestrationPropertiesAPIView.as_view(),
        name='cloudaccount-global-orchestration-properties'),

    url(r'^accounts/(?P<pk>[0-9]+)/formula_versions/$',
        api.CloudAccountFormulaVersionsAPIView.as_view(),
        name='cloudaccount-formula-versions'),

    url(r'^accounts/(?P<pk>[0-9]+)/permissions/',
        include(account_object_router.urls)),

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
