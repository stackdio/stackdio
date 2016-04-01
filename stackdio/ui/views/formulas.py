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

from stackdio.api.formulas.models import Formula
from stackdio.ui.views import PageView, ModelPermissionsView, ObjectPermissionsView
from stackdio.ui.utils import get_object_list


class FormulaImportView(PageView):
    template_name = 'formulas/formula-import.html'
    viewmodel = 'viewmodels/formula-import'

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm('formulas.create_formula'):
            # No permission granted
            raise Http404()
        return super(FormulaImportView, self).get(request, *args, **kwargs)


class FormulaListView(PageView):
    template_name = 'formulas/formula-list.html'
    viewmodel = 'viewmodels/formula-list'

    def get_context_data(self, **kwargs):
        context = super(FormulaListView, self).get_context_data(**kwargs)
        context['has_admin'] = self.request.user.has_perm('formulas.admin_formula')
        context['has_create'] = self.request.user.has_perm('formulas.create_formula')
        context['object_list'] = get_object_list(self.request.user, Formula)
        return context


class FormulaModelPermissionsView(ModelPermissionsView):
    viewmodel = 'viewmodels/formula-model-permissions'
    model = Formula


class FormulaDetailView(PageView):
    template_name = 'formulas/formula-detail.html'
    viewmodel = 'viewmodels/formula-detail'
    page_id = 'detail'

    def get_context_data(self, **kwargs):
        context = super(FormulaDetailView, self).get_context_data(**kwargs)
        pk = kwargs['pk']
        # Go ahead an raise a 404 here if the formula doesn't exist rather
        # than waiting until later.
        formula = get_object_or_404(Formula.objects.all(), pk=pk)
        if not self.request.user.has_perm('formulas.view_formula', formula):
            raise Http404()
        context['formula'] = formula
        context['has_admin'] = self.request.user.has_perm('formulas.admin_formula', formula)
        context['has_delete'] = self.request.user.has_perm('formulas.delete_formula', formula)
        context['has_update'] = self.request.user.has_perm('formulas.update_formula', formula)
        context['page_id'] = self.page_id
        return context


class FormulaObjectPermissionsView(ObjectPermissionsView):
    template_name = 'formulas/formula-object-permissions.html'
    viewmodel = 'viewmodels/formula-object-permissions'
    page_id = 'permissions'

    def get_context_data(self, **kwargs):
        context = super(FormulaObjectPermissionsView, self).get_context_data(**kwargs)
        pk = kwargs['pk']
        # Go ahead an raise a 404 here if the formula doesn't exist rather
        # than waiting until later.
        formula = get_object_or_404(Formula.objects.all(), pk=pk)
        if not self.request.user.has_perm('formulas.admin_formula', formula):
            raise Http404()
        context['formula'] = formula
        context['has_admin'] = self.request.user.has_perm('formulas.admin_formula', formula)
        context['page_id'] = self.page_id
        return context

    def get_object(self):
        return get_object_or_404(Formula.objects.all(), pk=self.kwargs['pk'])


class FormulaPropertiesView(FormulaDetailView):
    template_name = 'formulas/formula-properties.html'
    viewmodel = 'viewmodels/formula-properties'
    page_id = 'properties'
