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

from django.conf.urls import url
from django.contrib.auth.views import login, logout_then_login

from stackdio.core.utils import cached_url
from . import views
from .views import accounts
from .views import blueprints
from .views import formulas
from .views import snapshots
from .views import stacks

auth_kwargs = {
    'template_name': 'stackdio/login.html',
}

urlpatterns = (
    cached_url(r'^$',
               views.RootView.as_view(),
               name='index'),

    cached_url(r'^login/$',
               login,
               auth_kwargs,
               name='login',
               user_sensitive=False),

    url(r'^logout/$',
        logout_then_login,
        name='logout'),

    cached_url(r'^js/main/(?P<vm>[\w/.-]+)\.js$',
               views.AppMainView.as_view(),
               name='js-main',
               user_sensitive=False),

    cached_url('^user/$',
               views.UserProfileView.as_view(),
               name='user-profile'),

    cached_url(r'^stacks/$',
               stacks.StackListView.as_view(),
               name='stack-list',
               timeout=30),

    cached_url(r'^stacks/create/$',
               stacks.StackCreateView.as_view(),
               name='stack-create'),

    cached_url(r'^stacks/permissions/$',
               stacks.StackModelPermissionsView.as_view(),
               name='stack-model-permissions'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/$',
               stacks.StackDetailView.as_view(),
               name='stack-detail',
               timeout=30),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/properties/$',
               stacks.StackPropertiesView.as_view(),
               name='stack-properties'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/labels/$',
               stacks.StackLabelsView.as_view(),
               name='stack-labels'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/hosts/$',
               stacks.StackHostsView.as_view(),
               name='stack-hosts'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/volumes/$',
               stacks.StackVolumesView.as_view(),
               name='stack-volumes'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/commands/$',
               stacks.StackCommandsView.as_view(),
               name='stack-commands'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/commands/(?P<command_pk>[0-9]+)/$',
               stacks.StackCommandDetailView.as_view(),
               name='stack-command-detail'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/access_rules/$',
               stacks.StackAccessRulesView.as_view(),
               name='stack-access-rules'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/formula_versions/$',
               stacks.StackFormulaVersionsView.as_view(),
               name='stack-formula-versions'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/permissions/$',
               stacks.StackObjectPermissionsView.as_view(),
               name='stack-object-permissions'),

    cached_url(r'^stacks/(?P<pk>[0-9]+)/logs/$',
               stacks.StackLogsView.as_view(),
               name='stack-logs'),

    cached_url(r'^blueprints/$',
               blueprints.BlueprintListView.as_view(),
               name='blueprint-list',
               timeout=30),

    cached_url(r'^blueprints/permissions/$',
               blueprints.BlueprintModelPermissionsView.as_view(),
               name='blueprint-model-permissions'),

    cached_url(r'^blueprints/(?P<pk>[0-9]+)/$',
               blueprints.BlueprintDetailView.as_view(),
               name='blueprint-detail',
               timeout=30),

    cached_url(r'^blueprints/(?P<pk>[0-9]+)/properties/$',
               blueprints.BlueprintPropertiesView.as_view(),
               name='blueprint-properties'),

    cached_url(r'^blueprints/(?P<pk>[0-9]+)/formula_versions/$',
               blueprints.BlueprintFormulaVersionsView.as_view(),
               name='blueprint-formula-versions'),

    cached_url(r'^blueprints/(?P<pk>[0-9]+)/permissions/$',
               blueprints.BlueprintObjectPermissionsView.as_view(),
               name='blueprint-object-permissions'),

    cached_url(r'^formulas/$',
               formulas.FormulaListView.as_view(),
               name='formula-list',
               timeout=30),

    cached_url(r'^formulas/import/$',
               formulas.FormulaImportView.as_view(),
               name='formula-import'),

    cached_url(r'^formulas/permissions/$',
               formulas.FormulaModelPermissionsView.as_view(),
               name='formula-model-permissions'),

    cached_url(r'^formulas/(?P<pk>[0-9]+)/$',
               formulas.FormulaDetailView.as_view(),
               name='formula-detail',
               timeout=30),

    cached_url(r'^formulas/(?P<pk>[0-9]+)/properties/$',
               formulas.FormulaPropertiesView.as_view(),
               name='formula-properties'),

    cached_url(r'^formulas/(?P<pk>[0-9]+)/permissions/$',
               formulas.FormulaObjectPermissionsView.as_view(),
               name='formula-object-permissions'),

    cached_url(r'^snapshots/$',
               snapshots.SnapshotListView.as_view(),
               name='snapshot-list',
               timeout=30),

    cached_url(r'^snapshots/create/$',
               snapshots.SnapshotCreateView.as_view(),
               name='snapshot-create'),

    cached_url(r'^snapshots/permissions/$',
               snapshots.SnapshotModelPermissionsView.as_view(),
               name='snapshot-model-permissions'),

    cached_url(r'^snapshots/(?P<pk>[0-9]+)/$',
               snapshots.SnapshotDetailView.as_view(),
               name='snapshot-detail',
               timeout=30),

    cached_url(r'^snapshots/(?P<pk>[0-9]+)/permissions/$',
               snapshots.SnapshotObjectPermissionsView.as_view(),
               name='snapshot-object-permissions'),

    cached_url(r'^accounts/$',
               accounts.AccountListView.as_view(),
               name='cloud-account-list',
               timeout=30),

    cached_url(r'^accounts/permissions/$',
               accounts.AccountModelPermissionsView.as_view(),
               name='cloud-account-model-permissions'),

    cached_url(r'^accounts/(?P<pk>[0-9]+)/$',
               accounts.AccountDetailView.as_view(),
               name='cloud-account-detail',
               timeout=30),

    cached_url(r'^accounts/(?P<pk>[0-9]+)/permissions/$',
               accounts.AccountObjectPermissionsView.as_view(),
               name='cloud-account-object-permissions'),
)
