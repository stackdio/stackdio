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

from django.http import Http404
from django.shortcuts import get_object_or_404

from stackdio.api.blueprints.models import Blueprint
from stackdio.api.stacks.models import Stack, StackCommand
from stackdio.ui.views import PageView, ModelPermissionsView, ObjectPermissionsView
from stackdio.ui.utils import get_object_list


class StackCreateView(PageView):
    template_name = 'stacks/stack-create.html'
    viewmodel = 'viewmodels/stack-create'

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm('stacks.create_stack'):
            # No permission granted
            raise Http404()
        return super(StackCreateView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(StackCreateView, self).get_context_data(**kwargs)

        blueprint_id = self.request.GET.get('blueprint')

        blueprint = None
        if blueprint_id:
            try:
                blueprint = Blueprint.objects.get(id=blueprint_id)
            except Blueprint.DoesNotExist:
                pass

        context['blueprint'] = blueprint
        return context


class StackListView(PageView):
    template_name = 'stacks/stack-list.html'
    viewmodel = 'viewmodels/stack-list'

    def get_context_data(self, **kwargs):
        context = super(StackListView, self).get_context_data(**kwargs)
        context['has_admin'] = self.request.user.has_perm('stacks.admin_stack')
        context['has_create'] = self.request.user.has_perm('stacks.create_stack')
        context['object_list'] = get_object_list(self.request.user, Stack)
        return context


class StackModelPermissionsView(ModelPermissionsView):
    viewmodel = 'viewmodels/stack-model-permissions'
    model = Stack


class StackDetailView(PageView):
    template_name = 'stacks/stack-detail.html'
    viewmodel = 'viewmodels/stack-detail'
    page_id = 'detail'

    def get_context_data(self, **kwargs):
        context = super(StackDetailView, self).get_context_data(**kwargs)
        pk = kwargs['pk']
        # Go ahead an raise a 404 here if the stack doesn't exist rather than waiting until later.
        stack = get_object_or_404(Stack.objects.all(), pk=pk)
        if not self.request.user.has_perm('stacks.view_stack', stack):
            raise Http404()
        context['stack'] = stack
        context['has_admin'] = self.request.user.has_perm('stacks.admin_stack', stack)
        context['has_delete'] = self.request.user.has_perm('stacks.delete_stack', stack)
        context['has_update'] = self.request.user.has_perm('stacks.update_stack', stack)
        context['page_id'] = self.page_id
        return context


class StackObjectPermissionsView(ObjectPermissionsView):
    template_name = 'stacks/stack-object-permissions.html'
    viewmodel = 'viewmodels/stack-object-permissions'
    page_id = 'permissions'

    def get_context_data(self, **kwargs):
        context = super(StackObjectPermissionsView, self).get_context_data(**kwargs)
        pk = kwargs['pk']
        # Go ahead an raise a 404 here if the stack doesn't exist rather than waiting until later.
        stack = get_object_or_404(Stack.objects.all(), pk=pk)
        if not self.request.user.has_perm('stacks.admin_stack', stack):
            raise Http404()
        context['stack'] = stack
        context['has_admin'] = self.request.user.has_perm('stacks.admin_stack', stack)
        context['page_id'] = self.page_id
        return context

    def get_object(self):
        return get_object_or_404(Stack.objects.all(), pk=self.kwargs['pk'])


class StackPropertiesView(StackDetailView):
    template_name = 'stacks/stack-properties.html'
    viewmodel = 'viewmodels/stack-properties'
    page_id = 'properties'


class StackLabelsView(StackDetailView):
    template_name = 'stacks/stack-labels.html'
    viewmodel = 'viewmodels/stack-labels'
    page_id = 'labels'


class StackHostsView(StackDetailView):
    template_name = 'stacks/stack-hosts.html'
    viewmodel = 'viewmodels/stack-hosts'
    page_id = 'hosts'


class StackVolumesView(StackDetailView):
    template_name = 'stacks/stack-volumes.html'
    viewmodel = 'viewmodels/stack-volumes'
    page_id = 'volumes'


class StackCommandsView(StackDetailView):
    template_name = 'stacks/stack-commands.html'
    viewmodel = 'viewmodels/stack-commands'
    page_id = 'commands'


class StackCommandDetailView(StackDetailView):
    template_name = 'stacks/stack-command-detail.html'
    viewmodel = 'viewmodels/stack-command-detail'
    page_id = 'commands'

    def get_context_data(self, **kwargs):
        context = super(StackCommandDetailView, self).get_context_data(**kwargs)
        pk = kwargs['command_pk']
        # Go ahead an raise a 404 here if the command doesn't exist rather than waiting until later.
        get_object_or_404(StackCommand.objects.all(), pk=pk)
        context['command_id'] = pk
        return context


class StackAccessRulesView(StackDetailView):
    template_name = 'stacks/stack-access-rules.html'
    viewmodel = 'viewmodels/stack-access-rules'
    page_id = 'access-rules'


class StackFormulaVersionsView(StackDetailView):
    template_name = 'stacks/stack-formula-versions.html'
    viewmodel = 'viewmodels/stack-formula-versions'
    page_id = 'formula-versions'


class StackLogsView(StackDetailView):
    template_name = 'stacks/stack-logs.html'
    viewmodel = 'viewmodels/stack-logs'
    page_id = 'logs'
