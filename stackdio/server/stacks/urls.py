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


from django.conf.urls import patterns, url

from . import api

urlpatterns = patterns(
    'stacks.api',

    url(r'^hosts/$',
        api.HostListAPIView.as_view(),
        name='host-list'),

    url(r'^hosts/(?P<pk>[0-9]+)/$',
        api.HostDetailAPIView.as_view(),
        name='host-detail'),

    url(r'^actions/(?P<pk>[0-9]+)/$',
        api.StackActionDetailAPIView.as_view(),
        name='stackaction-detail'),

    url(r'^actions/(?P<pk>[0-9]+)/zip/$',
        'stack_action_zip',
        name='stackaction-zip'),

    url(r'^stacks/$',
        api.StackListAPIView.as_view(),
        name='stack-list'),

    url(r'^admin/stacks/$',
        api.StackAdminListAPIView.as_view(),
        name='stack-admin-list'),

    url(r'^stacks/public/$',
        api.StackPublicListAPIView.as_view(),
        name='stack-public-list'),

    url(r'^stacks/(?P<pk>[0-9]+)/$',
        api.StackDetailAPIView.as_view(),
        name='stack-detail'),

    url(r'^stacks/(?P<pk>[0-9]+)/hosts/$',
        api.StackHostsAPIView.as_view(),
        name='stack-hosts'),

    url(r'^stacks/(?P<pk>[0-9]+)/fqdns/$',
        api.StackFQDNListAPIView.as_view(),
        name='stack-fqdns'),

    url(r'^stacks/(?P<pk>[0-9]+)/volumes/$',
        api.StackVolumesAPIView.as_view(),
        name='stack-volumes'),

    url(r'^stacks/(?P<pk>[0-9]+)/properties/$',
        api.StackPropertiesAPIView.as_view(),
        name='stack-properties'),

    url(r'^stacks/(?P<pk>[0-9]+)/history/$',
        api.StackHistoryAPIView.as_view(),
        name='stack-history'),

    url(r'^stacks/(?P<pk>[0-9]+)/provisioning_errors/$',
        api.StackProvisioningErrorsAPIView.as_view(),
        name='stack-provisioning-errors'),

    url(r'^stacks/(?P<pk>[0-9]+)/orchestration_errors/$',
        api.StackOrchestrationErrorsAPIView.as_view(),
        name='stack-orchestration-errors'),

    url(r'^stacks/(?P<pk>[0-9]+)/logs/$',
        api.StackLogsAPIView.as_view(),
        name='stack-logs'),

    url(r'^stacks/(?P<pk>[0-9]+)/logs/(?P<log>.*)$',
        api.StackLogsDetailAPIView.as_view(),
        name='stack-logs-detail'),

    url(r'^stacks/(?P<pk>[0-9]+)/action/$',
        api.StackActionAPIView.as_view(),
        name='stack-action'),
    
    url(r'^stacks/(?P<pk>[0-9]+)/actions/$',
        api.StackActionListAPIView.as_view(),
        name='stackaction-list'),

    url(r'^stacks/(?P<pk>[0-9]+)/security_groups/$',
        api.StackSecurityGroupsAPIView.as_view(),
        name='stack-security-groups'),
)
