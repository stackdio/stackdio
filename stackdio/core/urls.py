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

from django.conf.urls import include, url
from django.contrib.auth.views import login, logout_then_login

from stackdio.server import __version__
from . import api, views

auth_kwargs = {
    'template_name': 'stackdio/login.html',
    'extra_context': {'version': __version__},
}

urlpatterns = (
    url(r'^$',
        views.RootView.as_view(),
        name='index'),

    url(r'^login/$',
        login,
        auth_kwargs,
        name='login'),

    url(r'^logout/$',
        logout_then_login,
        name='logout'),

    url(r'^api/version/$',
        api.VersionAPIView.as_view(),
        name='version'),

    url(r'^js/main/(?P<vm>[\w/.-]+)\.js$',
        views.AppMainView.as_view(),
        name='js-main'),

    url(r'^stacks/', include('stackdio.api.stacks.ui_urls')),
    url(r'^', include('stackdio.api.users.ui_urls')),
)
