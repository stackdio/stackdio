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

# Need this so the stackdio import below doesn't get confused
from __future__ import absolute_import

from django import template
from django.conf import settings

from stackdio.server import __version__

register = template.Library()


@register.simple_tag
def stackdio_version():
    return '<span class="version">{0}</span>'.format(__version__)


@register.simple_tag
def viewmodel(viewmodel):
    require = '{0}stackdio/lib/bower_components/requirejs/require.js'.format(settings.STATIC_URL)
    if settings.DEBUG:
        app = '/js/main/{0}'.format(viewmodel)
    else:
        app = '{0}stackdio/build/{1}.js'.format(settings.STATIC_URL, viewmodel)

    return '<script data-main="{0}" src="{1}"></script>'.format(app, require)
