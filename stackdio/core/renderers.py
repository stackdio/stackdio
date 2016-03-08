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

import json
import logging

from rest_framework import renderers

logger = logging.getLogger(__name__)


class PlainTextRenderer(renderers.BaseRenderer):
    """
    Your basic text/plain renderer.
    """
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, (dict, list, tuple, set, frozenset)):
            data = json.dumps(data)
        return str(data).encode(self.charset)


class ZipRenderer(renderers.BaseRenderer):
    """
    Zip renderer
    """
    media_type = 'application/zip'
    format = 'zip'
    charset = None
    render_style = 'binary'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data
