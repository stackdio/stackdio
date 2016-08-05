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
"""stackdio URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import include, url
from django.contrib import admin

from stackdio.api.urls import get_error_handler

# Enable admin interface
admin.autodiscover()

urlpatterns = (
    # Grab the core URLs.  Basically just the version endpoint.
    url(r'^', include('stackdio.core.urls', namespace='stackdio')),

    # API v1 root endpoint -- add additional URLs to urls.py in the api module.
    url(r'^api/', include('stackdio.api.urls', namespace='api')),

    # Default login/logout views. Without this you won't get the login/logout links
    # in the browsable api.
    url(r'^api/', include('rest_framework.urls', namespace='rest_framework')),

    # Grab the ui URLs.  Stuff like index, login, logout, etc
    url(r'^', include('stackdio.ui.urls', namespace='ui')),

    # Admin interface
    url(r'^__private/admin/', include(admin.site.urls)),
)

# Override the default handlers
handler400 = get_error_handler(400)
handler403 = get_error_handler(403)
handler404 = get_error_handler(404)
handler500 = get_error_handler(500)
