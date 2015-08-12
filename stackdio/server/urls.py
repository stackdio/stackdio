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

# Enable admin interface
from django.contrib import admin
admin.autodiscover()


urlpatterns = (
    # Admin interface
    url(r'^__private/admin/', include(admin.site.urls)),

    # Grab the core URLs.  Basically just the version endpoint.
    url(r'^', include('stackdio.core.urls', namespace='stackdio')),

    # Grab the ui URLs.  Stuff like index, login, logout, etc
    url(r'^', include('stackdio.ui.urls', namespace='ui')),

    # API v1 root endpoint -- add additional URLs to urls.py in the api module.
    url(r'^api/', include('stackdio.api.urls', namespace='api')),
)
