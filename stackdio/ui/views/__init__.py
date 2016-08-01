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


import logging

from django.http import HttpResponseRedirect, Http404
from django.shortcuts import resolve_url
from django.views.generic import TemplateView

from stackdio.api.cloud.models import CloudAccount

logger = logging.getLogger(__name__)


class RootView(TemplateView):
    """
    We don't really have a home page, so let's redirect to either the
    stack or account page depending on certain cases
    """
    def get(self, request, *args, **kwargs):
        has_account_perm = request.user.has_perm('cloud.create_cloudaccount')

        if has_account_perm and CloudAccount.objects.count() == 0:
            # if the user has permission to create an account and there aren't any yet,
            # take them there
            redirect_view = 'ui:cloud-account-list'
        else:
            # Otherwise just go to stacks
            redirect_view = 'ui:stack-list'
        return HttpResponseRedirect(resolve_url(redirect_view))


class AppMainView(TemplateView):
    template_name = 'stackdio/js/main.js'
    content_type = 'application/javascript'


class PageView(TemplateView):
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
