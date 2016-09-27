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


user_model_router = routers.SimpleBulkRouter()
user_model_router.register(r'users',
                           api.UserModelUserPermissionsViewSet,
                           'user-model-user-permissions')
user_model_router.register(r'groups',
                           api.UserModelGroupPermissionsViewSet,
                           'user-model-group-permissions')


model_router = routers.SimpleBulkRouter()
model_router.register(r'users',
                      api.GroupModelUserPermissionsViewSet,
                      'group-model-user-permissions')
model_router.register(r'groups',
                      api.GroupModelGroupPermissionsViewSet,
                      'group-model-group-permissions')


object_router = routers.SimpleBulkRouter()
object_router.register(r'users',
                       api.GroupObjectUserPermissionsViewSet,
                       'group-object-user-permissions')
object_router.register(r'groups',
                       api.GroupObjectGroupPermissionsViewSet,
                       'group-object-group-permissions')


urlpatterns = (
    url(r'^users/$',
        api.UserListAPIView.as_view(),
        name='user-list'),

    url(r'^users/permissions/',
        include(user_model_router.urls)),

    url(r'^users/(?P<username>[\w.@+-]+)/$',
        api.UserDetailAPIView.as_view(),
        name='user-detail'),

    url(r'^users/(?P<parent_username>[\w.@+-]+)/groups/$',
        api.UserGroupListAPIView.as_view(),
        name='user-grouplist'),

    url(r'^groups/$',
        api.GroupListAPIView.as_view(),
        name='group-list'),

    url(r'^groups/permissions/',
        include(model_router.urls)),

    url(r'^groups/(?P<name>[\w.@+-]+)/$',
        api.GroupDetailAPIView.as_view(),
        name='group-detail'),

    url(r'^groups/(?P<parent_name>[\w.@+-]+)/permissions/',
        include(object_router.urls)),

    url(r'^groups/(?P<parent_name>[\w.@+-]+)/users/$',
        api.GroupUserListAPIView.as_view(),
        name='group-userlist'),

    url(r'^groups/(?P<parent_name>[\w.@+-]+)/action/$',
        api.GroupActionAPIView.as_view(),
        name='group-action'),

    url(r'^groups/(?P<parent_name>[\w.@+-]+)/channels/$',
        api.GroupChannelListAPIView.as_view(),
        name='group-channel-list'),

    url(r'^groups/(?P<parent_name>[\w.@+-]+)/channels/(?P<name>[\w.@+-]+)/$',
        api.GroupChannelDetailAPIView.as_view(),
        name='group-channel-detail'),

    url(r'^user/$',
        api.CurrentUserDetailAPIView.as_view(),
        name='currentuser-detail'),

    url(r'^user/channels/$',
        api.CurrentUserChannelListAPIView.as_view(),
        name='currentuser-channel-list'),

    url(r'^user/channels/(?P<name>[\w.@+-]+)/$',
        api.CurrentUserChannelDetailAPIView.as_view(),
        name='currentuser-channel-detail'),

    url(r'^user/password/$',
        api.ChangePasswordAPIView.as_view(),
        name='currentuser-password'),
)
