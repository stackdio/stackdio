import logging

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from core.exceptions import BadRequest

from . import tasks
from . import serializers
from . import models
from . import filters

logger = logging.getLogger(__name__)


class FormulaListAPIView(generics.ListCreateAPIView):
    model = models.Formula
    serializer_class = serializers.FormulaSerializer
    parser_classes = (JSONParser,)
    filter_class = filters.FormulaFilter

    def get_queryset(self):
        return self.request.user.formulas.all()

    def pre_save(self, obj):
        obj.owner = self.request.user

    def create(self, request, *args, **kwargs):
        uri = request.DATA.get('uri', '')
        formulas = request.DATA.get('formulas', [])
        public = request.DATA.get('public', False)

        if not uri and not formulas:
            raise BadRequest('A uri field or a list of URIs in the formulas '
                             'field is required.')
        if uri and formulas:
            raise BadRequest('uri and formulas fields can not be used '
                             'together.')
        if uri and not formulas:
            formulas = [uri]

        # check for duplicate uris
        errors = []
        for uri in formulas:
            try:
                self.model.objects.get(uri=uri, owner=request.user)
                errors.append('Duplicate formula detected: {0}'.format(uri))
            except self.model.DoesNotExist:
                pass

        if errors:
            raise BadRequest(errors)

        # create the object in the database and kick off a task
        formula_objs = []
        for uri in formulas:
            formula_obj = self.model.objects.create(
                owner=request.user,
                public=public,
                uri=uri,
                status=self.model.IMPORTING,
                status_detail='Importing formula...this could take a while.')

            # Import using asynchronous task
            tasks.import_formula.si(formula_obj.id)()
            formula_objs.append(formula_obj)

        return Response(self.get_serializer(formula_objs, many=True).data)


class FormulaPublicAPIView(generics.ListAPIView):
    model = models.Formula
    serializer_class = serializers.FormulaSerializer
    parser_classes = (JSONParser,)

    def get_queryset(self):
        return self.model.objects \
            .filter(public=True) \
            .exclude(owner=self.request.user)


class FormulaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):

    model = models.Formula
    serializer_class = serializers.FormulaSerializer
    parser_classes = (JSONParser,)

    def get_object(self):
        '''
        Return the formula if it's owned by the request user or
        if it's public...else we'll raise a 404
        '''
        return get_object_or_404(self.model,
                                 Q(owner=self.request.user) | Q(public=True),
                                 pk=self.kwargs.get('pk'))

    def update(self, request, *args, **kwargs):
        '''
        Override PUT requests to only allow the public field to be changed.
        '''
        formula = self.get_object()

        # Only the owner can submit PUT/PATCH requests
        if formula.owner != request.user:
            raise BadRequest('Only the owner of a formula may modify it.')

        public = request.DATA.get('public', None)
        if public is None or len(request.DATA) > 1:
            raise BadRequest('Only "public" field of a formula may be '
                             'modified.')

        if not isinstance(public, bool):
            raise BadRequest("'public' field must be a boolean value.")

        # Update formula's public field
        formula.public = public
        formula.save()

        return Response(self.get_serializer(formula).data)

    def delete(self, request, *args, **kwargs):
        '''
        Override the delete method to check for ownership.
        '''
        formula = self.get_object()
        if formula.owner != request.user:
            raise BadRequest('Only the owner of a formula may delete it.')

        # Check for resources depending on this formula

        return super(FormulaDetailAPIView, self).delete(request,
                                                        *args,
                                                        **kwargs)


class FormulaPropertiesAPIView(generics.RetrieveAPIView):

    model = models.Formula
    serializer_class = serializers.FormulaPropertiesSerializer

    def get_object(self):
        '''
        Return the formula if it's owned by the request user or
        if it's public...else we'll raise a 404
        '''
        return get_object_or_404(self.model,
                                 Q(owner=self.request.user) | Q(public=True),
                                 pk=self.kwargs.get('pk'))


class FormulaComponentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):

    model = models.FormulaComponent
    serializer_class = serializers.FormulaComponentSerializer
    parser_classes = (JSONParser,)

    def get_object(self):
        return get_object_or_404(self.model,
                                 pk=self.kwargs.get('pk'),
                                 formula__owner=self.request.user)
