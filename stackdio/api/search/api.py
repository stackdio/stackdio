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


import logging

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from rest_framework import generics, permissions
from rest_framework.filters import DjangoObjectPermissionsFilter
from rest_framework.response import Response
from rest_framework.reverse import reverse

from stackdio.api.blueprints.serializers import BlueprintSerializer
from stackdio.api.formulas.serializers import FormulaSerializer
from stackdio.api.stacks.serializers import StackSerializer
from . import serializers

logger = logging.getLogger(__name__)


SERIALIZER_MAP = {
    'formula': FormulaSerializer,
    'blueprint': BlueprintSerializer,
    'stack': StackSerializer,
}


class SearchAPIView(generics.ListAPIView):
    """
    Will search the configured fields on appropriate models for the search term provided in
    the `q` url parameter.

    Ex: GET `/api/search/?q=java`

    This will search for any formula, blueprint, stack, etc with a title/description/etc
    containing 'java'
    """
    serializer_class = serializers.SearchSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoObjectPermissionsFilter,)
    parser_classes = ()

    def get_queryset(self):
        # This is still kind of naive... needs to be better

        q = self.request.query_params.get('q', '')

        if not q:
            return []

        full_queryset = []

        for app, models in apps.all_models.items():
            for model_name, model_cls in models.items():
                if not hasattr(model_cls.objects, 'search'):
                    continue

                ctype = ContentType.objects.get_for_model(model_cls)

                # Pull out all the objects we don't have permission on
                searchable = self.filter_queryset(model_cls.objects.all())

                # Use our qset search method
                for obj in searchable.search(q):
                    full_queryset.append({
                        'type': ctype,
                        'title': obj.title,
                        'url': reverse('api:%s:%s-detail' % (app, model_name),
                                       kwargs={'pk': obj.pk},
                                       request=self.request),
                        'object': SERIALIZER_MAP[ctype.model](obj).data,
                    })

        return full_queryset

    def list(self, request, *args, **kwargs):
        """
        Override so that we don't filter the queryset here, that would be bad
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
