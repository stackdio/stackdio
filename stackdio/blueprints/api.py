import logging

from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from core.exceptions import BadRequest

from .serializers import BlueprintSerializer
from .models import Blueprint

from formulas.models import FormulaComponent
from cloud.models import Snapshot

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
        public = request.DATA.get('public', False)
        properties = request.DATA.get('properties', {})
        hosts = request.DATA.get('hosts', [])

        if not title:
            errors.setdefault('title', []).append('This field is required.')
        # check for duplicates
        elif Blueprint.objects.filter(owner=self.request.user, title=title).count():
            errors.setdefault('title', []).append(
                'A Blueprint with this title already exists in your account.'
            )

        if not description:
            errors.setdefault('description', []).append('This field is required.')

        if not isinstance(public, bool):
            errors.setdefault('public', []).append('This field must be a boolean.')
            
        if not isinstance(properties, dict):
            errors.setdefault('properties', []).append(
                'This field must be a JSON object.'
            )
        else:
            # user properties are not allowed to provide a __stackdio__ key
            if '__stackdio__' in properties:
                errors.setdefault('properties', []).append(
                    'The __stackdio__ key is reserved for system use.'
                )

        if not isinstance(hosts, list) or not hosts:
            errors.setdefault('hosts', []).append('This field is required.')
        elif hosts:
            host_ok = True
            for host in hosts:
                if not isinstance(host, dict):
                    errors.setdefault('hosts', []).append(
                        'Hosts must be a JSON object.'
                    )
                    host_ok = False
                    break

                formula_components = host.get('formula_components', [])
                access_rules = host.get('access_rules', [])
                volumes = host.get('volumes', [])

                if 'title' not in host or not host['title']:
                    errors.setdefault('hosts', []).append(
                        'Hosts must have a title field.'
                    )
                    host_ok = False
                if 'description' not in host or not host['description']:
                    errors.setdefault('hosts', []).append(
                        'Hosts must have a description field.'
                    )
                    host_ok = False
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
                if not isinstance(formula_components, list):
                    errors.setdefault('hosts', []).append(
                        'Host formula_components field must be a list of '
                        'formula component ids that are owned by you.'
                    )
                    host_ok = False

                # check ownership of formula components
                for component in formula_components:
                    if not isinstance(component, dict):
                        errors.setdefault('formula_components', []).append(
                            'Formula components must be objects with an id and optional order field.'
                        )
                        break

                    component_id = component.get('id')
                    if not component_id:
                        errors.setdefault('formula_components', []).append(
                            'Formula components must have an id field.'
                        )
                        break

                    try:
                        component_order = int(component.get('order', 0))
                        if component_order < 0:
                            errors.setdefault('formula_components', []).append(
                                'Formula components order field must be non-negative.'
                            )
                    except ValueError:
                        errors.setdefault('formula_components', []).append(
                            'Formula components order field must be a non-negative integer.'
                        )
                        
                    try:
                        FormulaComponent.objects.get(pk=component_id,
                                                     formula__owner=request.user)
                    except FormulaComponent.DoesNotExist:
                        errors.setdefault('formula_components', []).append(
                            'Formula component with id {0} does not exist.'.format(component_id)
                        )

                # Validating access rules
                rules_ok = True
                for rule in access_rules:
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

                # Validating volumes
                volumes_ok = True
                for volume in volumes:
                    if 'device' not in volume:
                        errors.setdefault('volumes', []).append(
                            'volumes must have a device field.'
                        )
                        volumes_ok = False
                    if 'mount_point' not in volume:
                        errors.setdefault('volumes', []).append(
                            'volumes must have a mount_point field.'
                        )
                        volumes_ok = False
                    if 'snapshot' not in volume:
                        errors.setdefault('volumes', []).append(
                            'volumes must have a snapshot field.'
                        )
                        volumes_ok = False
                    else:
                        volume['snapshot'] = Snapshot.objects.get(pk=volume['snapshot'])
                    if not volumes_ok:
                        break

                # Validating spot instances
                spot_ok = True
                spot_config = host.get('spot_config', None)
                if spot_config is not None and not isinstance(spot_config, dict):
                    errors.setdefault('spot_config', []).append(
                        'spot_config must be a JSON object and contain a '
                        'spot_price field.'
                    )
                elif spot_config is not None:
                    if 'spot_price' not in spot_config:
                        errors.setdefault('spot_config', []).append(
                            'spot_price must be set in spot_config.'
                        )
                    elif not isinstance(spot_config['spot_price'], float):
                        errors.setdefault('spot_config', []).append(
                            'spot_price must be a decimal value.' 
                        )
                    elif spot_config['spot_price'] < 0:
                        errors.setdefault('spot_config', []).append(
                            'spot_price must be a non-negative value.' 
                        )
                        
                if not host_ok or not rules_ok or not volumes_ok:
                    break

        if errors:
            raise BadRequest(errors)

        blueprint = Blueprint.objects.create(request.user, request.DATA)
        return Response(self.get_serializer(blueprint).data)


class BlueprintPublicAPIView(generics.ListAPIView):

    model = Blueprint
    serializer_class = BlueprintSerializer

    def get_queryset(self):
        return self.model.objects \
            .filter(public=True) \
            .exclude(owner=self.request.user)


class BlueprintDetailAPIView(generics.RetrieveUpdateDestroyAPIView):

    model = Blueprint
    serializer_class = BlueprintSerializer
    parser_classes = (JSONParser,)

    def get_object(self):
        # Return the blueprint if it's owned by the request user or
        # if it's public...else we'll raise a 404
        return get_object_or_404(self.model,
                                 Q(owner=self.request.user) | Q(public=True),
                                 pk=self.kwargs.get('pk'))

    def update(self, request, *args, **kwargs):
        blueprint = self.get_object()

        # Only the owner of the blueprint can submit PUT/PATCH requests
        if blueprint.owner != request.user:
            raise BadRequest('Only the owner of a blueprint may modify it.')

        # rebuild properties list
        properties = request.DATA.get('properties', None)
        if isinstance(properties, list):
            with transaction.commit_on_success():
                blueprint.properties.all().delete()
                for name, value in set([(p['name'], p['value']) for p in properties]):
                    blueprint.properties.create(name=name, value=value)

        # since we have already updated the properties list, trick super::update
        # method into thinking no properties have changed
        request.DATA['properties'] = []
        return super(BlueprintDetailAPIView, self).update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        '''
        Override the delete method to check for ownership.
        '''
        blueprint = self.get_object()
        if blueprint.owner != request.user:
            raise BadRequest('Only the owner of a blueprint may delete it.')
        return super(BlueprintDetailAPIView, self).delete(request, *args, **kwargs)

