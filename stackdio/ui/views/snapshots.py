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

from stackdio.api.cloud.models import Snapshot
from stackdio.ui.views import PageView, ModelPermissionsView, ObjectPermissionsView
from stackdio.ui.utils import get_object_list


class SnapshotCreateView(PageView):
    template_name = 'snapshots/snapshot-create.html'
    viewmodel = 'viewmodels/snapshot-create'

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm('cloud.create_snapshot'):
            # No permission granted
            raise Http404()
        return super(SnapshotCreateView, self).get(request, *args, **kwargs)


class SnapshotListView(PageView):
    template_name = 'snapshots/snapshot-list.html'
    viewmodel = 'viewmodels/snapshot-list'

    def get_context_data(self, **kwargs):
        context = super(SnapshotListView, self).get_context_data(**kwargs)
        context['has_admin'] = self.request.user.has_perm('cloud.admin_snapshot')
        context['has_create'] = self.request.user.has_perm('cloud.create_snapshot')
        context['object_list'] = get_object_list(self.request.user, Snapshot)
        return context


class SnapshotModelPermissionsView(ModelPermissionsView):
    viewmodel = 'viewmodels/snapshot-model-permissions'
    model = Snapshot


class SnapshotDetailView(PageView):
    template_name = 'snapshots/snapshot-detail.html'
    viewmodel = 'viewmodels/snapshot-detail'
    page_id = 'detail'

    def get_context_data(self, **kwargs):
        context = super(SnapshotDetailView, self).get_context_data(**kwargs)
        pk = kwargs['pk']
        # Go ahead an raise a 404 here if the snapshot doesn't exist rather
        # than waiting until later.
        snapshot = get_object_or_404(Snapshot.objects.all(), pk=pk)
        if not self.request.user.has_perm('cloud.view_snapshot', snapshot):
            raise Http404()
        context['snapshot'] = snapshot
        context['has_admin'] = self.request.user.has_perm('cloud.admin_snapshot', snapshot)
        context['has_delete'] = self.request.user.has_perm('cloud.delete_snapshot', snapshot)
        context['has_update'] = self.request.user.has_perm('cloud.update_snapshot', snapshot)
        context['page_id'] = self.page_id
        return context


class SnapshotObjectPermissionsView(ObjectPermissionsView):
    template_name = 'snapshots/snapshot-object-permissions.html'
    viewmodel = 'viewmodels/snapshot-object-permissions'
    page_id = 'permissions'

    def get_context_data(self, **kwargs):
        context = super(SnapshotObjectPermissionsView, self).get_context_data(**kwargs)
        pk = kwargs['pk']
        # Go ahead an raise a 404 here if the snapshot doesn't exist rather
        # than waiting until later.
        snapshot = get_object_or_404(Snapshot.objects.all(), pk=pk)
        if not self.request.user.has_perm('cloud.admin_snapshot', snapshot):
            raise Http404()
        context['snapshot'] = snapshot
        context['has_admin'] = self.request.user.has_perm('cloud.admin_snapshot', snapshot)
        context['page_id'] = self.page_id
        return context

    def get_object(self):
        return get_object_or_404(Snapshot.objects.all(), pk=self.kwargs['pk'])
