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


import logging

from django.shortcuts import redirect
from django.views.generic import TemplateView

from stackdio.server import __version__

logger = logging.getLogger(__name__)


class StackdioView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(StackdioView, self).get_context_data(**kwargs)
        context['version'] = __version__
        return context


class RootView(StackdioView):
    template_name = 'stackdio/home.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return super(RootView, self).get(request, *args, **kwargs)
        else:
            return redirect('login')
