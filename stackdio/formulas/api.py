# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import logging
from urlparse import urlsplit, urlunsplit

from guardian.shortcuts import assign_perm
from rest_framework import generics, status
from rest_framework.filters import DjangoFilterBackend, DjangoObjectPermissionsFilter
from rest_framework.response import Response

from blueprints.serializers import BlueprintSerializer
from core.exceptions import BadRequest
from core.viewsets import StackdioObjectPermissionsViewSet
from core.permissions import StackdioModelPermissions, StackdioObjectPermissions
from core.serializers import StackdioUserPermissionsSerializer, StackdioGroupPermissionsSerializer
from . import filters, mixins, models, permissions, serializers, tasks, utils


logger = logging.getLogger(__name__)

GLOBAL_ORCHESTRATION_USER = '__stackdio__'


# TODO Rewrite the logic in this endpoint
class FormulaListAPIView(generics.ListCreateAPIView):
    """
    Displays a list of all formulas visible to you.
    """
    queryset = models.Formula.objects.all()
    serializer_class = serializers.FormulaSerializer
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.FormulaFilter

    def create(self, request, *args, **kwargs):
        uri = request.DATA.get('uri')
        git_username = request.DATA.get('git_username', '')
        git_password = request.DATA.get('git_password', '')
        access_token = request.DATA.get('access_token', False)

        if not uri:
            raise BadRequest('A uri field is required.')

        # check for duplicate uris
        try:
            models.Formula.objects.get(uri=uri)
            raise BadRequest('Duplicate formula detected: {0}'.format(uri))
        except models.Formula.DoesNotExist:
            pass

        # create the object in the database and kick off a task
        if git_username != '':
            if not access_token and not git_password:
                raise BadRequest('Your git password is required if you\'re not using an '
                                 'access token.')
            if access_token and git_password:
                raise BadRequest('If you are using an access token, you may not provide a '
                                 'password.')

            # Add the git username to the uri if necessary
            parse_res = urlsplit(uri)
            if '@' not in parse_res.netloc:
                new_netloc = '{0}@{1}'.format(git_username, parse_res.netloc)
                uri = urlunsplit((
                    parse_res.scheme,
                    new_netloc,
                    parse_res.path,
                    parse_res.query,
                    parse_res.fragment
                ))

        formula_obj = models.Formula(
            uri=uri,
            git_username=git_username,
            access_token=access_token,
            status=models.Formula.IMPORTING,
            status_detail='Importing formula...this could take a while.')

        formula_obj.save()

        # Assign permissions so the user that just created the formula can operate on it
        for perm in models.Formula.object_permissions:
            assign_perm('formulas.%s_formula' % perm, request.user, formula_obj)

        # Import using asynchronous task
        tasks.import_formula.si(formula_obj.id, utils.PasswordStr(git_password)).apply_async()

        return Response(self.get_serializer(formula_obj).data)


class FormulaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Formula.objects.all()
    serializer_class = serializers.FormulaSerializer
    permission_classes = (StackdioObjectPermissions,)

    def update(self, request, *args, **kwargs):
        """
        Override PUT requests to only allow the public field to be changed.
        """
        formula = self.get_object()

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
        """
        Override the delete method to check for ownership and prevent
        delete if other resources depend on this formula or one
        of its components.
        """
        formula = self.get_object()

        # Check for Blueprints depending on this formula
        blueprints = set()
        for c in formula.components.all():
            blueprints.update(
                [i.host.blueprint for i in c.blueprinthostformulacomponent_set.all()])

        if blueprints:
            blueprints = BlueprintSerializer(blueprints,
                                             context={'request': request}).data
            return Response({
                'detail': 'One or more blueprints are making use of this '
                          'formula.',
                'blueprints': blueprints,
            }, status=status.HTTP_400_BAD_REQUEST)

        return super(FormulaDetailAPIView, self).delete(request, *args, **kwargs)


class FormulaPropertiesAPIView(mixins.FormulaRelatedMixin, generics.RetrieveAPIView):
    queryset = models.Formula.objects.all()
    serializer_class = serializers.FormulaPropertiesSerializer


class FormulaComponentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.FormulaComponent.objects.all()
    serializer_class = serializers.FormulaComponentSerializer
    permission_classes = (permissions.FormulaParentObjectPermissions,)

    def check_object_permissions(self, request, obj):
        # Check the permissions on the formula instead of the component
        super(FormulaComponentDetailAPIView, self).check_object_permissions(request, obj.formula)


class FormulaActionAPIView(mixins.FormulaRelatedMixin, generics.GenericAPIView):
    queryset = models.Formula.objects.all()
    serializer_class = serializers.FormulaSerializer

    AVAILABLE_ACTIONS = [
        'update',
    ]

    def get(self, request, *args, **kwargs):
        return Response({
            'available_actions': self.AVAILABLE_ACTIONS
        })

    def post(self, request, *args, **kwargs):
        formula = self.get_formula()
        action = request.DATA.get('action', None)

        if not action:
            raise BadRequest('action is a required parameter')

        if action not in self.AVAILABLE_ACTIONS:
            raise BadRequest('{0} is not an available action'.format(action))

        if action == 'update':
            git_password = request.DATA.get('git_password', '')
            if formula.private_git_repo and not formula.access_token:
                if git_password == '':
                    # User didn't provide a password
                    raise BadRequest('Your git password is required to '
                                     'update from a private repository.')

            formula.set_status(models.Formula.IMPORTING,
                               'Importing formula...this could take a while.')
            tasks.update_formula.si(formula.id, utils.PasswordStr(git_password)).apply_async()

        return Response(self.get_serializer(formula).data)


class FormulaUserPermissionsViewSet(mixins.FormulaRelatedMixin, StackdioObjectPermissionsViewSet):
    serializer_class = StackdioUserPermissionsSerializer
    permission_classes = (permissions.FormulaPermissionsObjectPermissions,)
    user_or_group = 'user'
    lookup_field = 'username'


class FormulaGroupPermissionsViewSet(mixins.FormulaRelatedMixin, StackdioObjectPermissionsViewSet):
    serializer_class = StackdioGroupPermissionsSerializer
    permission_classes = (permissions.FormulaPermissionsObjectPermissions,)
    user_or_group = 'group'
    lookup_field = 'groupname'
