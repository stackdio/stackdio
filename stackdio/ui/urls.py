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

from django.conf.urls import url
from django.contrib.auth.views import login, logout_then_login

from stackdio.core.utils import cached_url
from . import views

auth_kwargs = {
    'template_name': 'stackdio/login.html',
}

urlpatterns = (
    cached_url(r'^$',
               views.RootView.as_view(),
               name='index'),

    cached_url(r'^login/$',
               login,
               auth_kwargs,
               name='login',
               user_sensitive=False),

    url(r'^logout/$',
        logout_then_login,
        name='logout'),

    cached_url(r'^js/main/(?P<vm>[\w/.-]+)\.js$',
               views.AppMainView.as_view(),
               name='js-main',
               user_sensitive=False),

    cached_url('^user/$',
               views.UserProfileView.as_view(),
               name='user-profile'),

    cached_url(r'^stacks/$',
               views.StackListView.as_view(),
               name='stack-list',
               timeout=30),

    cached_url(r'^stacks/create/$',
               views.StackCreateView.as_view(),
               name='stack-create'),

    cached_url(r'^stacks/permissions/$',
               views.StackModelPermissionsView.as_view(),
               name='stack-model-permissions'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/$',
               views.StackDetailView.as_view(),
               name='stack-detail',
               timeout=30),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/properties/$',
               views.StackPropertiesView.as_view(),
               name='stack-properties'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/hosts/$',
               views.StackHostsView.as_view(),
               name='stack-hosts'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/volumes/$',
               views.StackVolumesView.as_view(),
               name='stack-volumes'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/commands/$',
               views.StackCommandsView.as_view(),
               name='stack-commands'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/permissions/$',
               views.StackObjectPermissionsView.as_view(),
               name='stack-object-permissions'),
)
