import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from core.exceptions import BadRequest, ResourceConflict

from . import tasks
from .serializers import FormulaSerializer, FormulaComponentSerializer
from .models import Formula, FormulaComponent

logger = logging.getLogger(__name__)


class FormulaListAPIView(generics.ListCreateAPIView):

    model = Formula
    serializer_class = FormulaSerializer
    parser_classes = (JSONParser,)

    def get_queryset(self):
        return self.request.user.formulas.all()

    def pre_save(self, obj):
        obj.owner = self.request.user

    def create(self, request, *args, **kwargs):
        uri = request.DATA.get('uri', '')
        public = request.DATA.get('public', False)

        if not uri:
            raise BadRequest('uri field is required')

        # check for duplicate uri
        try:
            formula = Formula.objects.get(uri=uri, owner=request.user)
            raise ResourceConflict('A formula already exists with this '
                                   'uri: {0}'.format(uri))
        except Formula.DoesNotExist:
            pass

        formula = Formula.objects.create(owner=request.user,
                                         public=public,
                                         uri=uri,
                                         status=Formula.IMPORTING,
                                         status_detail='Importing formula...this could take a while.')

        # Import using asynchronous task
        tasks.import_formula.si(formula.id)()

        return Response(self.get_serializer(formula).data)


class FormulaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):

    model = Formula
    serializer_class = FormulaSerializer
    parser_classes = (JSONParser,)

    def get_object(self):
        return get_object_or_404(Formula,
                                 pk=self.kwargs.get('pk'),
                                 owner=self.request.user)

    def update(self, request, *args, **kwargs):
        '''
        Override PUT requests to only allow the public field to be changed.
        '''
        public = request.DATA.get('public', None)
        if public is None or len(request.DATA) > 1:
            raise BadRequest("Only 'public' field of a formula may be modified.")

        if not isinstance(public, bool):
            raise BadRequest("'public' field must be a boolean value.")


        # Update formula's public field
        formula = self.get_object()
        formula.public = public
        formula.save()

        return Response(self.get_serializer(formula).data)


class FormulaComponentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):

    model = FormulaComponent
    serializer_class = FormulaComponentSerializer
    parser_classes = (JSONParser,)

    def get_object(self):
        return get_object_or_404(FormulaComponent,
                                 pk=self.kwargs.get('pk'),
                                 formula__owner=self.request.user)

