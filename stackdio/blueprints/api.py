import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from core.exceptions import BadRequest

from .serializers import BlueprintSerializer
from .models import Blueprint
from formulas.models import FormulaComponent

logger = logging.getLogger(__name__)


class BlueprintListAPIView(generics.ListCreateAPIView):

    model = Blueprint
    serializer_class = BlueprintSerializer
    parser_classes = (JSONParser,)

    def get_queryset(self):
        return self.request.user.blueprints.all()

    def pre_save(self, obj):
        obj.owner = self.request.user

    def create(self, request, *args, **kwargs):
        errors = {}
        title = request.DATA.get('title', '')
        description = request.DATA.get('description', '')
        properties = request.DATA.get('properties', [])
        hosts = request.DATA.get('hosts', [])

        if not title:
            errors.setdefault('title', []).append('This field is required.')

        if not description:
            errors.setdefault('description', []).append('This field is required.')

        if not properties or not isinstance(properties, list):
            errors.setdefault('properties', []).append(
                'This field is required and must be a list of properties.'
            )
        else:
            for prop in properties:
                if 'name' not in prop or 'value' not in prop:
                    errors.setdefault('properties', []).append(
                        'Properties must have both a name and value field.'
                    )
                    break

        if not isinstance(hosts, list) or not hosts:
            errors.setdefault('hosts', []).append('This field is required.')
        elif hosts:
            host_ok = True
            for host in hosts:
                if 'count' not in host:
                    errors.setdefault('hosts', []).append(
                        'Hosts must have a count field.'
                    )
                    host_ok = False
                if 'size' not in host:
                    errors.setdefault('hosts', []).append(
                        'Hosts must have a size field.'
                    )
                    host_ok = False
                if 'prefix' not in host:
                    errors.setdefault('hosts', []).append(
                        'Hosts must have a prefix field.'
                    )
                    host_ok = False
                if 'zone' not in host:
                    errors.setdefault('hosts', []).append(
                        'Hosts must have a zone field.'
                    )
                    host_ok = False
                if 'cloud_profile' not in host:
                    errors.setdefault('hosts', []).append(
                        'Hosts must have a cloud_profile field.'
                    )
                    host_ok = False
                if 'formula_components' not in host:
                    errors.setdefault('hosts', []).append(
                        'Hosts must have a formula_components field.'
                    )
                    host_ok = False
                elif not host['formula_components'] or \
                     not isinstance(host['formula_components'], list):
                    errors.setdefault('hosts', []).append(
                        'Host formula_components field must be a list of existing formula component ids that are owned by you.'
                    )
                    host_ok = False

                # check ownership of formula components
                for component_id in host['formula_components']:
                    try:
                        FormulaComponent.objects.get(pk=component_id,
                                                     formula__owner=request.user)
                    except FormulaComponent.DoesNotExist:
                        errors.setdefault('formula_components', []).append(
                            'Formula component with id {0} does not exist.'.format(component_id)
                        )

                if 'access_rules' in host and isinstance(host['access_rules'], list):
                    rules_ok = True
                    for rule in host['access_rules']:
                        if 'protocol' not in rule:
                            errors.setdefault('access_rules', []).append(
                                'access_rules must have a protocol field.'                
                            )
                            rules_ok = False
                        if 'from_port' not in rule:
                            errors.setdefault('access_rules', []).append(
                                'access_rules must have a from_port field.'                
                            )
                            rules_ok = False
                        if 'to_port' not in rule:
                            errors.setdefault('access_rules', []).append(
                                'access_rules must have a to_port field.'                
                            )
                            rules_ok = False
                        if 'rule' not in rule:
                            errors.setdefault('access_rules', []).append(
                                'access_rules must have a rule field.'                
                            )
                            rules_ok = False
                        if not rules_ok:
                            break

                if not host_ok or not rules_ok:
                    break

        if errors:
            raise BadRequest(errors)

        blueprint = Blueprint.objects.create(request.user, request.DATA)
        return Response(self.get_serializer(blueprint).data)


class BlueprintDetailAPIView(generics.RetrieveUpdateDestroyAPIView):

    model = Blueprint
    serializer_class = BlueprintSerializer
    parser_classes = (JSONParser,)

    def get_object(self):
        return get_object_or_404(Blueprint,
                                 pk=self.kwargs.get('pk'),
                                 owner=self.request.user)

    def update(self, request, *args, **kwargs):
        blueprint = self.get_object()
        properties = request.DATA.get('properties', None)

        # rebuild properties list
        if isinstance(properties, list):
            with transaction.commit_on_success():
                blueprint.properties.all().delete()
                for name, value in set([(p['name'], p['value']) for p in properties]):
                    blueprint.properties.create(name=name, value=value)

        # since we have already updated the properties list, trick super::update
        # method into thinking no properties have changed
        request.DATA['properties'] = []
        return super(BlueprintDetailAPIView, self).update(request, *args, **kwargs)
