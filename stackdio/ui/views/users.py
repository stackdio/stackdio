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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import Http404
from django.shortcuts import get_object_or_404

from stackdio.ui.views import PageView, ModelPermissionsView, ObjectPermissionsView
from stackdio.ui.utils import get_object_list


class FailOnLDAPMixin(object):
    def render_to_response(self, context, **response_kwargs):
        if settings.LDAP_ENABLED:
            self.template_name = 'users/ldap-managed.html'
            response_kwargs['status'] = 400
        return super(FailOnLDAPMixin, self).render_to_response(context, **response_kwargs)


class UserProfileView(PageView):
    template_name = 'users/user-profile.html'
    viewmodel = 'viewmodels/user-profile'

    def get_context_data(self, **kwargs):
        context = super(UserProfileView, self).get_context_data(**kwargs)
        context['ldap'] = settings.LDAP_ENABLED
        return context


class UserPasswordChangeView(FailOnLDAPMixin, PageView):
    template_name = 'users/user-password-change.html'
    viewmodel = 'viewmodels/user-password-change'


class UserCreateView(FailOnLDAPMixin, PageView):
    template_name = 'users/user-create.html'
    viewmodel = 'viewmodels/user-create'

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm('auth.create_user'):
            # No permission granted
            raise Http404()
        return super(UserCreateView, self).get(request, *args, **kwargs)


class UserListView(PageView):
    template_name = 'users/user-list.html'
    viewmodel = 'viewmodels/user-list'

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context['has_admin'] = self.request.user.has_perm('auth.admin_user')
        context['has_create'] = self.request.user.has_perm('auth.create_user')
        context['ldap_enabled'] = settings.LDAP_ENABLED
        return context


class UserModelPermissionsView(ModelPermissionsView):
    viewmodel = 'viewmodels/user-model-permissions'
    model = get_user_model()


class GroupCreateView(PageView):
    template_name = 'users/group-create.html'
    viewmodel = 'viewmodels/group-create'

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm('auth.create_group'):
            # No permission granted
            raise Http404()
        return super(GroupCreateView, self).get(request, *args, **kwargs)


class GroupListView(PageView):
    template_name = 'users/group-list.html'
    viewmodel = 'viewmodels/group-list'

    def get_context_data(self, **kwargs):
        context = super(GroupListView, self).get_context_data(**kwargs)
        context['has_admin'] = self.request.user.has_perm('auth.admin_group')
        context['has_create'] = self.request.user.has_perm('auth.create_group')
        context['object_list'] = get_object_list(self.request.user, Group, 'name')
        return context


class GroupModelPermissionsView(ModelPermissionsView):
    viewmodel = 'viewmodels/group-model-permissions'
    model = Group


class GroupDetailView(PageView):
    template_name = 'users/group-detail.html'
    viewmodel = 'viewmodels/group-detail'
    page_id = 'detail'

    def get_context_data(self, **kwargs):
        context = super(GroupDetailView, self).get_context_data(**kwargs)
        name = kwargs['name']
        # Go ahead an raise a 404 here if the group doesn't exist rather than waiting until later.
        group = get_object_or_404(Group.objects.all(), name=name)
        if not self.request.user.has_perm('auth.view_group', group):
            raise Http404()
        context['group'] = group
        context['has_admin'] = self.request.user.has_perm('auth.admin_group', group)
        context['has_delete'] = self.request.user.has_perm('auth.delete_group', group)
        context['has_update'] = self.request.user.has_perm('auth.update_group', group)
        context['page_id'] = self.page_id
        return context


class GroupObjectPermissionsView(ObjectPermissionsView):
    template_name = 'users/group-object-permissions.html'
    viewmodel = 'viewmodels/group-object-permissions'
    page_id = 'permissions'

    def get_context_data(self, **kwargs):
        context = super(GroupObjectPermissionsView, self).get_context_data(**kwargs)
        name = kwargs['name']
        # Go ahead an raise a 404 here if the group doesn't exist rather than waiting until later.
        group = get_object_or_404(Group.objects.all(), name=name)
        if not self.request.user.has_perm('auth.admin_group', group):
            raise Http404()
        context['group'] = group
        context['object_id'] = name
        context['has_admin'] = self.request.user.has_perm('auth.admin_group', group)
        context['page_id'] = self.page_id
        return context

    def get_object(self):
        return get_object_or_404(Group.objects.all(), name=self.kwargs['name'])


class GroupMembersView(GroupDetailView):
    template_name = 'users/group-members.html'
    viewmodel = 'viewmodels/group-members'
    page_id = 'members'
