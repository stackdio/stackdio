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
from stackdio.api.cloud.models import CloudAccount
from stackdio.ui.utils import get_object_list
from stackdio.ui.views import (
    PageView,
    ObjectDetailView,
    ModelPermissionsView,
    ObjectPermissionsView,
)


class AccountCreateView(PageView):
    template_name = 'cloud/cloud-account-create.html'
    viewmodel = 'viewmodels/cloud-account-create'

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm('cloud.create_cloudaccount'):
            # No permission granted
            raise Http404()
        return super(AccountCreateView, self).get(request, *args, **kwargs)


class AccountListView(PageView):
    template_name = 'cloud/cloud-account-list.html'
    viewmodel = 'viewmodels/cloud-account-list'

    def get_context_data(self, **kwargs):
        context = super(AccountListView, self).get_context_data(**kwargs)
        context['has_admin'] = self.request.user.has_perm('cloud.admin_cloudaccount')
        context['has_create'] = self.request.user.has_perm('cloud.create_cloudaccount')
        context['object_list'] = get_object_list(self.request.user, CloudAccount)
        return context


class AccountModelPermissionsView(ModelPermissionsView):
    viewmodel = 'viewmodels/cloud-account-model-permissions'
    model = CloudAccount


class AccountDetailView(ObjectDetailView):
    template_name = 'cloud/cloud-account-detail.html'
    viewmodel = 'viewmodels/cloud-account-detail'
    page_id = 'detail'

    model = CloudAccount
    model_verbose_name = 'Cloud Account'
    model_short_name = 'account'


class AccountObjectPermissionsView(ObjectPermissionsView):
    template_name = 'cloud/cloud-account-object-permissions.html'
    viewmodel = 'viewmodels/cloud-account-object-permissions'
    page_id = 'permissions'

    def get_context_data(self, **kwargs):
        context = super(AccountObjectPermissionsView, self).get_context_data(**kwargs)
        pk = kwargs['pk']
        # Go ahead an raise a 404 here if the account doesn't exist rather
        # than waiting until later.
        account = get_object_or_404(CloudAccount.objects.all(), pk=pk)
        if not self.request.user.has_perm('cloud.admin_cloudaccount', account):
            raise Http404()
        context['account'] = account
        context['has_admin'] = self.request.user.has_perm('cloud.admin_cloudaccount', account)
        context['page_id'] = self.page_id
        return context

    def get_object(self):
        return get_object_or_404(CloudAccount.objects.all(), pk=self.kwargs['pk'])


class AccountImagesView(AccountDetailView):
    template_name = 'cloud/cloud-account-images.html'
    viewmodel = 'viewmodels/cloud-account-images'
    page_id = 'images'


class AccountSecurityGroupsView(AccountDetailView):
    template_name = 'cloud/cloud-account-security-groups.html'
    viewmodel = 'viewmodels/cloud-account-security-groups'
    page_id = 'security-groups'
