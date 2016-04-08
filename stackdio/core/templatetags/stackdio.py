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

# Need this so the stackdio import below doesn't get confused
from __future__ import absolute_import

from django import template
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.shortcuts import resolve_url
from django.utils.safestring import mark_safe

from stackdio.server import __version__

register = template.Library()


@register.simple_tag
def stackdio_version():
    return mark_safe('<span class="version">{0}</span>'.format(__version__))


@register.simple_tag
def main_file():
    if settings.JAVASCRIPT_DEBUG:
        return resolve_url('ui:js-main')
    else:
        return static('stackdio/build/main.js')
