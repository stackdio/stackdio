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

# from django.http import Http404

from stackdio.ui.views import PageView


# class UserCreateView(PageView):
#     template_name = 'users/user-create.html'
#     viewmodel = 'viewmodels/user-create'
#
#     def get(self, request, *args, **kwargs):
#         if not request.user.has_perm('auth.create_user'):
#             # No permission granted
#             raise Http404()
#         return super(UserCreateView, self).get(request, *args, **kwargs)


class UserListView(PageView):
    template_name = 'users/user-list.html'
    viewmodel = 'viewmodels/user-list'

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context['has_admin'] = self.request.user.has_perm('auth.admin_user')
        context['has_create'] = self.request.user.has_perm('auth.create_user')
        return context
