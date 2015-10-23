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
from django.shortcuts import resolve_url
from django.views.generic import TemplateView

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
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect('/stacks/')
        else:
            redirect_url = resolve_url('ui:login')
            if request.path != '/':
                redirect_url = '{0}?next={1}'.format(redirect_url, request.path)
            return HttpResponseRedirect(redirect_url)


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
        context['object_id'] = kwargs.get('pk')
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
