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


from django.conf.urls import patterns, include, url

# Enable admin interface
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    # Main application
    url(r'^$', 'core.views.index', name='index'),

    # Session views
    url(r'^login/$', 'core.views.login', name='login'),
    url(r'^logout/$', 'core.views.logout', name='logout'),

    # Admin interface
    url(r'^__private/admin/', include(admin.site.urls)),

    # API v1 root endpoint -- add additional URLs to urls.py in
    # the api_v1 module.
    url(r'^api/', include('api_v1.urls')),
    # url(r'^api-docs/', include('rest_framework_swagger.urls')),

    # Default login/logout views. Without this you won't get the login/logout links
    # in the views.
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
)
