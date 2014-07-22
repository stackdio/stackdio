import logging
from urlparse import urlsplit, urlunsplit

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
import keyring

from core.exceptions import BadRequest
from core.permissions import AdminOrOwnerOrPublicPermission
from blueprints.serializers import BlueprintSerializer
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
        git_username = request.DATA.get('git_username', '')
        git_password = request.DATA.get('git_password', '')
        save_git_password = request.DATA.get('save_git_password', False)

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
            if git_username != '':
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

                # Store the password in the keyring if the user wishes
                #   Use the uri as the service in case there are two accounts
                #   with the same username and different passwords
                #   (i.e.) github and bitbucket with the same username,
                #       different pass
                if save_git_password:
                    keyring.set_password(uri,
                                         git_username,
                                         git_password)

            formula_obj = self.model.objects.create(
                owner=request.user,
                public=public,
                uri=uri,
                git_username=git_username,
                status=self.model.IMPORTING,
                status_detail='Importing formula...this could take a while.')

            # Import using asynchronous task
            tasks.import_formula.si(formula_obj.id, git_password)()
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


class FormulaAdminListAPIView(generics.ListAPIView):
    model = models.Formula
    serializer_class = serializers.FormulaSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return self.model.objects.all()


class FormulaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):

    model = models.Formula
    serializer_class = serializers.FormulaSerializer
    parser_classes = (JSONParser,)
    permission_classes = (permissions.IsAuthenticated,
                          AdminOrOwnerOrPublicPermission,)

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
            blueprints.update([i.host.blueprint for i in c.blueprinthostformulacomponent_set.all()])

        if blueprints:
            blueprints = BlueprintSerializer(blueprints,
                                             context={'request': request}).data
            return Response({
                'detail': 'One or more blueprints are making use of this '
                          'formula.',
                'blueprints': blueprints,
            }, status=status.HTTP_400_BAD_REQUEST)

        return super(FormulaDetailAPIView, self).delete(request,
                                                        *args,
                                                        **kwargs)


class FormulaPropertiesAPIView(generics.RetrieveAPIView):

    model = models.Formula
    serializer_class = serializers.FormulaPropertiesSerializer
    permission_classes = (permissions.IsAuthenticated,
                          AdminOrOwnerOrPublicPermission,)


class FormulaComponentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):

    model = models.FormulaComponent
    serializer_class = serializers.FormulaComponentSerializer
    parser_classes = (JSONParser,)
    permission_classes = (permissions.IsAuthenticated,
                          AdminOrOwnerOrPublicPermission,)


class FormulaActionAPIView(generics.SingleObjectAPIView):
    model = models.Formula
    serializer_class = serializers.FormulaSerializer
    permission_classes = (permissions.IsAuthenticated,
                          AdminOrOwnerOrPublicPermission)

    AVAILABLE_ACTIONS = [
        'update'
    ]

    def get(self, request, *args, **kwargs):
        return Response({
            'available_actions': self.AVAILABLE_ACTIONS
        })

    def post(self, request, *args, **kwargs):
        formula = self.get_object()
        action = request.DATA.get('action', None)
        git_password = request.DATA.get('git_password', '')

        if not action:
            raise BadRequest('action is a required parameter')

        if action not in self.AVAILABLE_ACTIONS:
            raise BadRequest('{0} is not an available action'.format(action))

        if formula.private_git_repo:
            if not formula.git_password_stored and git_password == '':
                # No password is stored and user didn't provide a password
                raise BadRequest('Your git password is required to update from a private repository.')
            else:
                git_password = keyring.get_password(formula.uri, formula.git_username)

        if action == 'update':
            formula.set_status(models.Formula.IMPORTING, 'Importing formula...this could take a while.')
            tasks.update_formula.si(formula.id, git_password)()

        return Response(self.get_serializer(formula).data)

