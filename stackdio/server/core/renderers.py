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


from django.utils.encoding import smart_unicode
from rest_framework import renderers

class PlainTextRenderer(renderers.BaseRenderer):
    """
    Your basic text/plain renderer.
    """
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None):
        if isinstance(data, basestring):
            return data
        return smart_unicode(data)

class XMLRenderer(PlainTextRenderer):
    """
    Subclass PlainTextRenderer, but switch to XML content-type. DRF has a built-in
    XMLRenderer, but it wants to put everything inside of a <root> tag.
    """
    media_type = 'application/xml'
    format = 'xml'

class JSONRenderer(PlainTextRenderer):
    """
    Subclass PlainTextRenderer, but switch to JSON content-type. Need a way to
    quickly pass JSON strings out without running through deserializer.
    """
    media_type = 'application/json'
    format = 'json'
