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
from stackdio.ui.views import PageView, ModelPermissionsView, ObjectPermissionsView
from stackdio.ui.utils import get_object_list


class BlueprintListView(PageView):
    template_name = 'blueprints/blueprint-list.html'
    viewmodel = 'viewmodels/blueprint-list'

    def get_context_data(self, **kwargs):
        context = super(BlueprintListView, self).get_context_data(**kwargs)
        context['has_admin'] = self.request.user.has_perm('blueprints.admin_blueprint')
        context['has_create'] = self.request.user.has_perm('blueprints.create_blueprint')
        context['object_list'] = get_object_list(self.request.user, Blueprint)
        return context


class BlueprintModelPermissionsView(ModelPermissionsView):
    viewmodel = 'viewmodels/blueprint-model-permissions'
    model = Blueprint


class BlueprintDetailView(PageView):
    template_name = 'blueprints/blueprint-detail.html'
    viewmodel = 'viewmodels/blueprint-detail'
    page_id = 'detail'

    def get_context_data(self, **kwargs):
        context = super(BlueprintDetailView, self).get_context_data(**kwargs)
        pk = kwargs['pk']
        # Go ahead an raise a 404 here if the blueprint doesn't exist rather
        # than waiting until later.
        blueprint = get_object_or_404(Blueprint.objects.all(), pk=pk)
        if not self.request.user.has_perm('blueprints.view_blueprint', blueprint):
            raise Http404()
        context['blueprint'] = blueprint
        context['has_admin'] = self.request.user.has_perm('blueprints.admin_blueprint', blueprint)
        context['has_delete'] = self.request.user.has_perm('blueprints.delete_blueprint', blueprint)
        context['has_update'] = self.request.user.has_perm('blueprints.update_blueprint', blueprint)
        context['page_id'] = self.page_id
        return context


class BlueprintObjectPermissionsView(ObjectPermissionsView):
    template_name = 'blueprints/blueprint-object-permissions.html'
    viewmodel = 'viewmodels/blueprint-object-permissions'
    page_id = 'permissions'

    def get_context_data(self, **kwargs):
        context = super(BlueprintObjectPermissionsView, self).get_context_data(**kwargs)
        pk = kwargs['pk']
        # Go ahead an raise a 404 here if the blueprint doesn't exist rather
        # than waiting until later.
        blueprint = get_object_or_404(Blueprint.objects.all(), pk=pk)
        if not self.request.user.has_perm('blueprints.admin_blueprint', blueprint):
            raise Http404()
        context['blueprint'] = blueprint
        context['has_admin'] = self.request.user.has_perm('blueprints.admin_blueprint', blueprint)
        context['page_id'] = self.page_id
        return context

    def get_object(self):
        return get_object_or_404(Blueprint.objects.all(), pk=self.kwargs['pk'])


class BlueprintPropertiesView(BlueprintDetailView):
    template_name = 'blueprints/blueprint-properties.html'
    viewmodel = 'viewmodels/blueprint-properties'
    page_id = 'properties'


class BlueprintLabelsView(BlueprintDetailView):
    template_name = 'blueprints/blueprint-labels.html'
    viewmodel = 'viewmodels/blueprint-labels'
    page_id = 'labels'


class BlueprintHostDefinitionsView(BlueprintDetailView):
    template_name = 'blueprints/blueprint-host-definitions.html'
    viewmodel = 'viewmodels/blueprint-host-definitions'
    page_id = 'host-definitions'


class BlueprintFormulaVersionsView(BlueprintDetailView):
    template_name = 'blueprints/blueprint-formula-versions.html'
    viewmodel = 'viewmodels/blueprint-formula-versions'
    page_id = 'formula-versions'
