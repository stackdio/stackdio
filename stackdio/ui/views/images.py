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

from stackdio.api.cloud.models import CloudImage
from stackdio.ui.views import PageView, ModelPermissionsView, ObjectPermissionsView
from stackdio.ui.utils import get_object_list


class ImageCreateView(PageView):
    template_name = 'cloud/cloud-image-create.html'
    viewmodel = 'viewmodels/cloud-image-create'

    def get(self, request, *args, **kwargs):
        if not request.user.has_perm('cloud.create_cloudimage'):
            # No permission granted
            raise Http404()
        return super(ImageCreateView, self).get(request, *args, **kwargs)


class ImageListView(PageView):
    template_name = 'cloud/cloud-image-list.html'
    viewmodel = 'viewmodels/cloud-image-list'

    def get_context_data(self, **kwargs):
        context = super(ImageListView, self).get_context_data(**kwargs)
        context['has_admin'] = self.request.user.has_perm('cloud.admin_cloudimage')
        context['has_create'] = self.request.user.has_perm('cloud.create_cloudimage')
        context['object_list'] = get_object_list(self.request.user, CloudImage)
        return context


class ImageModelPermissionsView(ModelPermissionsView):
    viewmodel = 'viewmodels/cloud-image-model-permissions'
    model = CloudImage


class ImageDetailView(PageView):
    template_name = 'cloud/cloud-image-detail.html'
    viewmodel = 'viewmodels/cloud-image-detail'
    page_id = 'detail'

    def get_context_data(self, **kwargs):
        context = super(ImageDetailView, self).get_context_data(**kwargs)
        pk = kwargs['pk']
        # Go ahead an raise a 404 here if the image doesn't exist rather
        # than waiting until later.
        image = get_object_or_404(CloudImage.objects.all(), pk=pk)
        if not self.request.user.has_perm('cloud.view_cloudimage', image):
            raise Http404()
        context['image'] = image
        context['has_admin'] = self.request.user.has_perm('cloud.admin_cloudimage', image)
        context['has_delete'] = self.request.user.has_perm('cloud.delete_cloudimage', image)
        context['has_update'] = self.request.user.has_perm('cloud.update_cloudimage', image)
        context['page_id'] = self.page_id
        return context


class ImageObjectPermissionsView(ObjectPermissionsView):
    template_name = 'cloud/cloud-image-object-permissions.html'
    viewmodel = 'viewmodels/cloud-image-object-permissions'
    page_id = 'permissions'

    def get_context_data(self, **kwargs):
        context = super(ImageObjectPermissionsView, self).get_context_data(**kwargs)
        pk = kwargs['pk']
        # Go ahead an raise a 404 here if the image doesn't exist rather
        # than waiting until later.
        image = get_object_or_404(CloudImage.objects.all(), pk=pk)
        if not self.request.user.has_perm('cloud.admin_cloudimage', image):
            raise Http404()
        context['image'] = image
        context['has_admin'] = self.request.user.has_perm('cloud.admin_cloudimage', image)
        context['page_id'] = self.page_id
        return context

    def get_object(self):
        return get_object_or_404(CloudImage.objects.all(), pk=self.kwargs['pk'])
