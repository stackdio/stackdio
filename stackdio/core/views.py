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

from django.shortcuts import resolve_url
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from stackdio.server import __version__

logger = logging.getLogger(__name__)


class StackdioView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(StackdioView, self).get_context_data(**kwargs)
        context['version'] = __version__
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return super(StackdioView, self).get(request, *args, **kwargs)
        else:
            redirect_url = resolve_url('login')
            if request.path != '/':
                redirect_url = '{0}?next={1}'.format(redirect_url, request.path)
            return HttpResponseRedirect(redirect_url)


class RootView(StackdioView):
    template_name = 'stackdio/home.html'


class PageView(StackdioView):
    viewmodel = None

    def __init__(self, **kwargs):
        super(PageView, self).__init__(**kwargs)
        assert self.viewmodel is not None, ('You must specify a viewmodel via the `viewmodel` '
                                            'attribute of your class.')

    def get_context_data(self, **kwargs):
        context = super(PageView, self).get_context_data(**kwargs)
        context['viewmodel'] = 'stackdio/app/viewmodels/%s.js' % self.viewmodel
        return context


class StackListView(PageView):
    template_name = 'stackdio/stack-list.html'
    viewmodel = 'stack-list'
