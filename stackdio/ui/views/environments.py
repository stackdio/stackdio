# -*- coding: utf-8 -*-

# Copyright 2017,  Digital Reasoning
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

from __future__ import unicode_literals

from django.http import Http404
from django.shortcuts import get_object_or_404
from stackdio.api.environments.models import Environment
from stackdio.ui.utils import get_object_list
from stackdio.ui.views import (
    PageView,
    ObjectDetailView,
    ModelPermissionsView,
    ObjectPermissionsView,
)


class EnvironmentCreateView(PageView):
    template_name = 'environments/environment-create.html'
    viewmodel = 'viewmodels/environment-create'

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm('environments.create_environment'):
            # No permission granted
            raise Http404()
        return super(EnvironmentCreateView, self).get(request, *args, **kwargs)


class EnvironmentListView(PageView):
    template_name = 'environments/environment-list.html'
    viewmodel = 'viewmodels/environment-list'

    def get_context_data(self, **kwargs):
        context = super(EnvironmentListView, self).get_context_data(**kwargs)
        context['has_admin'] = self.request.user.has_perm('environments.admin_environment')
        context['has_create'] = self.request.user.has_perm('environments.create_environment')
        context['object_list'] = get_object_list(self.request.user, Environment)
        return context


class EnvironmentModelPermissionsView(ModelPermissionsView):
    viewmodel = 'viewmodels/environment-model-permissions'
    model = Environment


class EnvironmentDetailView(ObjectDetailView):
    template_name = 'environments/environment-detail.html'
    viewmodel = 'viewmodels/environment-detail'
    page_id = 'detail'

    model = Environment
    model_verbose_name = 'Environment'
    model_short_name = 'environment'
    lookup_field = 'name'


class EnvironmentObjectPermissionsView(ObjectPermissionsView):
    template_name = 'environments/environment-object-permissions.html'
    viewmodel = 'viewmodels/environment-object-permissions'
    page_id = 'permissions'

    def get_context_data(self, **kwargs):
        context = super(EnvironmentObjectPermissionsView, self).get_context_data(**kwargs)
        name = kwargs['name']
        # Go ahead an raise a 404 here if the environment doesn't exist rather
        # than waiting until later.
        environment = get_object_or_404(Environment.objects.all(), name=name)
        if not self.request.user.has_perm('environments.admin_environment', environment):
            raise Http404()
        context['environment'] = environment
        context['has_admin'] = self.request.user.has_perm('environments.admin_environment',
                                                          environment)
        context['page_id'] = self.page_id

        # override the object id
        context['object_id'] = name
        return context

    def get_object(self):
        return get_object_or_404(Environment.objects.all(), name=self.kwargs['name'])


class EnvironmentPropertiesView(EnvironmentDetailView):
    template_name = 'environments/environment-properties.html'
    viewmodel = 'viewmodels/environment-properties'
    page_id = 'properties'


class EnvironmentHostsView(EnvironmentDetailView):
    template_name = 'environments/environment-hosts.html'
    viewmodel = 'viewmodels/environment-hosts'
    page_id = 'hosts'


class EnvironmentLabelsView(EnvironmentDetailView):
    template_name = 'environments/environment-labels.html'
    viewmodel = 'viewmodels/environment-labels'
    page_id = 'labels'


class EnvironmentComponentsView(EnvironmentDetailView):
    template_name = 'environments/environment-components.html'
    viewmodel = 'viewmodels/environment-components'
    page_id = 'components'


class EnvironmentFormulaVersionsView(EnvironmentDetailView):
    template_name = 'environments/environment-formula-versions.html'
    viewmodel = 'viewmodels/environment-formula-versions'
    page_id = 'formula-versions'


class EnvironmentLogsView(EnvironmentDetailView):
    template_name = 'environments/environment-logs.html'
    viewmodel = 'viewmodels/environment-logs'
    page_id = 'logs'
