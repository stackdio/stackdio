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


import logging

from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import settings as rest_settings
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.pagination import PaginationSerializer

from core.exceptions import BadRequest, ResourceConflict

from . import serializers
from blueprints.models import Blueprint
from formulas.models import Formula
from stacks.models import Stack

logger = logging.getLogger(__name__)


class SearchAPIView(generics.SingleObjectAPIView):
    # Don't accept any form of parseable input
    parser_classes = ()

    def get(self, request, *args, **kwargs):
        res = []
        q = request.QUERY_PARAMS.get('q', '')
        context = {'request': request}

        # pull the pagination page index from settings/defaults or the query params
        try:
            page_index = int(request.QUERY_PARAMS.get('page', 1))
        except ValueError:
            page_index = 1

        # pull the pagination page size from settings/defaults or the query params
        try:
            page_size = int(request.QUERY_PARAMS.get(
                settings.REST_FRAMEWORK.get('PAGINATE_BY_PARAM', 'page_size'),
                settings.REST_FRAMEWORK.get('PAGINATE_BY', 10)
            ))
        except ValueError:
            page_size = 10

        if q:
            # finds all matching blueprints that are owned by the user or
            # have been made public
            blueprints = Blueprint.objects.filter(
                Q(owner=request.user) | Q(public=True),
                Q(title__icontains=q) | Q(description__icontains=q)
            ).order_by('created')
            res.extend(serializers.BlueprintSearchSerializer(blueprints, many=True, context=context).data)

            # finds all matching formulas that are owned by the user or
            # have been made public
            formulas = Formula.objects.filter(
                Q(owner=request.user) | Q(public=True),
                Q(title__icontains=q) | Q(description__icontains=q)
            ).order_by('created')
            res.extend(serializers.FormulaSearchSerializer(formulas, many=True, context=context).data)

            # finds all matching stacks that are owned by the user
            stacks = Stack.objects.filter(
                Q(title__icontains=q) | Q(description__icontains=q),
                owner=request.user
            ).order_by('created')
            res.extend(serializers.StackSearchSerializer(stacks, many=True, context=context).data)

        # add in pagination and render the serialized and paginated data
        # paginator = Paginator(res, page_size)
        # page = paginator.page(page_index)
        # serializer = PaginationSerializer(instance=page, context=context)
        # serializer = PaginationSerializer(instance=page, context=context)
        return Response(res)

