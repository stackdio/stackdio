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

from stackdio.api.blueprints.models import Blueprint
from stackdio.ui.views import PageView, ModelPermissionsView


class BlueprintListView(PageView):
    template_name = 'blueprints/blueprint-list.html'
    viewmodel = 'viewmodels/blueprint-list'

    def get_context_data(self, **kwargs):
        context = super(BlueprintListView, self).get_context_data(**kwargs)
        context['has_admin'] = self.request.user.has_perm('blueprints.admin_blueprint')
        context['has_create'] = self.request.user.has_perm('blueprints.create_blueprint')
        return context


class BlueprintModelPermissionsView(ModelPermissionsView):
    viewmodel = 'viewmodels/blueprint-model-permissions'
    model = Blueprint
