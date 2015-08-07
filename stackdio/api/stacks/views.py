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

from stackdio.core.views import PageView

logger = logging.getLogger(__name__)


class StackListView(PageView):
    template_name = 'stacks/stack-list.html'
    viewmodel = 'viewmodels/stack-list'


class StackDetailView(PageView):
    template_name = 'stacks/stack-detail.html'
    viewmodel = 'viewmodels/stack-detail'

    def get_context_data(self, **kwargs):
        context = super(StackDetailView, self).get_context_data(**kwargs)
        context['stack_id'] = kwargs['pk']
        return context
