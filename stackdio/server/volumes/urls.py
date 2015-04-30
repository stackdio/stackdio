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

from .api import (
    VolumeListAPIView,
    VolumeDetailAPIView,
    VolumeAdminListAPIView,
)

urlpatterns = patterns('volumes.api',

    url(r'^volumes/$',
        VolumeListAPIView.as_view(),
        name='volume-list'),

    url(r'^volumes/(?P<pk>[0-9]+)/$',
        VolumeDetailAPIView.as_view(),
        name='volume-detail'),

    url(r'^admin/volumes/$',
        VolumeAdminListAPIView.as_view(),
        name='volume-admin-list'),
)
