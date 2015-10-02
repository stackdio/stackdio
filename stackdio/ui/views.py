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

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, resolve_url
from django.views.generic import TemplateView

from stackdio.api.stacks.models import Stack, StackCommand

logger = logging.getLogger(__name__)


class StackdioView(TemplateView):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return super(StackdioView, self).get(request, *args, **kwargs)
        else:
            redirect_url = resolve_url('ui:login')
            if request.path != '/':
                redirect_url = '{0}?next={1}'.format(redirect_url, request.path)
            return HttpResponseRedirect(redirect_url)


class RootView(StackdioView):
    template_name = 'stackdio/home.html'


class AppMainView(TemplateView):
    template_name = 'stackdio/js/main.js'
    content_type = 'application/javascript'

    def __init__(self, **kwargs):
        super(AppMainView, self).__init__(**kwargs)
        self.viewmodel = None

    def get_context_data(self, **kwargs):
        context = super(AppMainView, self).get_context_data(**kwargs)
        context['viewmodel'] = self.viewmodel
        return context

    def get(self, request, *args, **kwargs):
        self.viewmodel = kwargs.get('vm')
        if self.viewmodel is None:
            return HttpResponse()
        return super(AppMainView, self).get(request, *args, **kwargs)


class PageView(StackdioView):
    viewmodel = None

    def __init__(self, **kwargs):
        super(PageView, self).__init__(**kwargs)
        assert self.viewmodel is not None, (
            'You must specify a viewmodel via the `viewmodel` '
            'attribute of your class.'
        )

    def get_context_data(self, **kwargs):
        context = super(PageView, self).get_context_data(**kwargs)
        context['viewmodel'] = self.viewmodel
        return context


class ModelPermissionsView(PageView):
    template_name = 'stackdio/permissions.html'
    model = None

    def __init__(self, **kwargs):
        super(ModelPermissionsView, self).__init__(**kwargs)
        assert self.model is not None, (
            'You must specify a model via the `model` '
            'attribute of your class.'
        )

    def get_context_data(self, **kwargs):
        context = super(ModelPermissionsView, self).get_context_data(**kwargs)
        model_name = self.model._meta.model_name
        context['object_type'] = model_name.capitalize()
        return context

    def get(self, request, *args, **kwargs):
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        if not request.user.has_perm('%s.admin_%s' % (app_label, model_name)):
            # No permission granted
            raise Http404()
        return super(ModelPermissionsView, self).get(request, *args, **kwargs)


class ObjectPermissionsView(PageView):
    template_name = 'stackdio/permissions.html'

    def get_object(self):
        raise NotImplementedError()

    def get_context_data(self, **kwargs):
        context = super(ObjectPermissionsView, self).get_context_data(**kwargs)
        context['object_type'] = self.get_object()._meta.model_name.capitalize()
        context['object_id'] = kwargs['pk']
        return context

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        app_label = obj._meta.app_label
        model_name = obj._meta.model_name
        # Check permissions on the object
        if not request.user.has_perm('%s.admin_%s' % (app_label, model_name), obj):
            # No permission granted
            raise Http404()
        return super(ObjectPermissionsView, self).get(request, *args, **kwargs)


class UserProfileView(PageView):
    template_name = 'users/user-profile.html'
    viewmodel = 'viewmodels/user-profile'

    def get_context_data(self, **kwargs):
        context = super(UserProfileView, self).get_context_data(**kwargs)
        context['ldap'] = settings.LDAP_ENABLED
        return context


class StackCreateView(PageView):
    template_name = 'stacks/stack-create.html'
    viewmodel = 'viewmodels/stack-create'

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm('stacks.create_stack'):
            # No permission granted
            raise Http404()
        return super(StackCreateView, self).get(request, *args, **kwargs)


class StackListView(PageView):
    template_name = 'stacks/stack-list.html'
    viewmodel = 'viewmodels/stack-list'

    def get_context_data(self, **kwargs):
        context = super(StackListView, self).get_context_data(**kwargs)
        context['has_admin'] = self.request.user.has_perm('stacks.admin_stack')
        context['has_create'] = self.request.user.has_perm('stacks.create_stack')
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
        context['stack_id'] = pk
        context['has_admin'] = self.request.user.has_perm('stacks.admin_stack', stack)
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
        if not self.request.user.has_perm('stacks.view_stack', stack):
            raise Http404()
        context['stack_id'] = pk
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
