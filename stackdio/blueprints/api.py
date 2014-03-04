import logging
import string

from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from core.exceptions import BadRequest

from . import serializers
from . import models
from . import filters

from formulas.models import FormulaComponent
from cloud.models import Snapshot
from stacks.serializers import StackSerializer

logger = logging.getLogger(__name__)


# TODO: need to move these somewhere else
VAR_NAMESPACE = 'namespace'
VAR_USERNAME = 'username'
VAR_INDEX = 'index'
VALID_TEMPLATE_VARS = (VAR_NAMESPACE, VAR_USERNAME, VAR_INDEX)
VALID_PROTOCOLS = ('tcp', 'udp', 'icmp')


class OwnerOrPublicPermission(permissions.BasePermission):
    '''
    A permission that allows safe methods through for public objects
    and all access to owners.
    '''
    def has_object_permission(self, request, view, obj):
        if request.user == obj.owner:
            return True
        if not obj.public:
            return False
        return request.method == 'GET'


class PublicBlueprintMixin(object):
    permission_classes = (permissions.IsAuthenticated,
                          OwnerOrPublicPermission,)

    def get_object(self):
        obj = get_object_or_404(models.Blueprint, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj


class BlueprintListAPIView(generics.ListCreateAPIView):

    model = models.Blueprint
    serializer_class = serializers.BlueprintSerializer
    parser_classes = (JSONParser,)
    filter_class = filters.BlueprintFilter

    def get_queryset(self):
        return self.request.user.blueprints.all()

    def pre_save(self, obj):
        obj.owner = self.request.user

    # TODO: Ignoring code complexity issues
    def create(self, request, *args, **kwargs): # NOQA
        errors = {}
        title = request.DATA.get('title', '')
        description = request.DATA.get('description', '')
        public = request.DATA.get('public', False)
        properties = request.DATA.get('properties', {})
        hosts = request.DATA.get('hosts', [])

        if not title:
            errors.setdefault('title', []).append('This is a required field.')
        # check for duplicates
        elif models.Blueprint.objects.filter(owner=self.request.user,
                                             title=title).count():
            errors.setdefault('title', []).append(
                'A Blueprint with this title already exists in your account.'
            )

        if not description:
            errors.setdefault('description', []).append(
                'This is a required field.')

        if not isinstance(public, bool):
            errors.setdefault('public', []).append(
                'This field must be a boolean.')

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
            errors.setdefault('hosts', []).append('This is a required field.')
        elif hosts:
            host_titles = []

            for host_index, host in enumerate(hosts):
                host_string = 'hosts[{0}]'.format(host_index)
                if not isinstance(host, dict):
                    errors.setdefault(host_string, []).append(
                        'Host definition must be a JSON object.'
                    )
                    continue

                formula_components = host.get('formula_components', [])
                access_rules = host.get('access_rules', [])
                volumes = host.get('volumes', [])

                if 'title' not in host or not host['title']:
                    errors.setdefault(host_string + '.title', []).append(
                        'This is a required field.'
                    )
                elif host['title'] in host_titles:
                    errors.setdefault(host_string + '.title', []).append(
                        'Duplicate title. Each host title must be unique.'
                    )
                else:
                    host_titles.append(host['title'])
                if 'description' not in host or not host['description']:
                    errors.setdefault(host_string + '.description', []).append(
                        'This is a required field.'
                    )
                if 'count' not in host:
                    errors.setdefault(host_string + '.count', []).append(
                        'This is a required field.'
                    )
                elif not isinstance(host['count'], int):
                    errors.setdefault(host_string + '.count', []).append(
                        'Must be a non-negative integer.'
                    )
                if 'size' not in host:
                    errors.setdefault(host_string + '.size', []).append(
                        'This is a required field.'
                    )
                elif not isinstance(host['size'], int):
                    errors.setdefault(host_string + '.size', []).append(
                        'Must be a non-negative integer.'
                    )
                # check the size instance
                else:
                    try:
                        models.CloudInstanceSize.objects.get(pk=host['size'])
                    except models.CloudInstanceSize.DoesNotExist:
                        errors.setdefault(host_string + '.size', []).append(
                            'Instance size with id {0} does not exist.'
                            .format(host['size'])
                        )
                if 'hostname_template' not in host:
                    errors.setdefault(host_string + '.hostname_template', []) \
                        .append('This is a required field.')
                else:
                    # check for valid hostname_template variables
                    f = string.Formatter()
                    vars = [x[1] for x in f.parse(
                        host['hostname_template']
                    ) if x[1]]
                    invalid_vars = [x for x in vars
                                    if x not in VALID_TEMPLATE_VARS]

                    if invalid_vars:
                        errors.setdefault(host_string + '.hostname_template',
                                          []) \
                            .append('Invalid variables found: {0}'.format(
                                ', '.join(invalid_vars)
                            ))

                    # VAR_INDEX must be present if host count is greater than
                    # one
                    if host.get('count', 0) > 1 and VAR_INDEX not in vars:
                        errors.setdefault(host_string + '.hostname_template',
                                          []).append(
                            'Variable {0} must be specified for hosts with '
                            'a count greater than one.'.format(VAR_INDEX)
                        )

                if 'zone' not in host:
                    errors.setdefault(host_string + '.zone', []).append(
                        'This is a required field.'
                    )
                elif not isinstance(host['zone'], int):
                    errors.setdefault(host_string + '.zone', []).append(
                        'Must be a non-negative integer.'
                    )
                # check the zone instance
                else:
                    try:
                        models.CloudZone.objects.get(pk=host['zone'])
                    except models.CloudZone.DoesNotExist:
                        errors.setdefault(host_string + '.zone', []).append(
                            'Zone with id {0} does not exist.'.format(
                                host['size']))

                if 'cloud_profile' not in host:
                    errors.setdefault(host_string + '.cloud_profile', []) \
                        .append('This is a required field.')
                elif not isinstance(host['cloud_profile'], int):
                    errors.setdefault(host_string + '.cloud_profile', []) \
                        .append('Must be a non-negative integer.')
                # check the cloud profile instance
                else:
                    try:
                        models.CloudProfile.objects.get(
                            pk=host['cloud_profile'])
                    except models.CloudProfile.DoesNotExist:
                        errors.setdefault(host_string + '.cloud_profile', []) \
                            .append('Profile with id {0} '
                                    'does not exist.'.format(host['size']))
                if not isinstance(formula_components, list):
                    errors.setdefault(host_string + '.formula_components',
                                      []).append('Must be a list of objects '
                                                 'with an id and optional '
                                                 'order field.')
                else:
                    # check ownership of formula components
                    for component in formula_components:
                        if not isinstance(component, dict):
                            errors.setdefault(
                                host_string + '.formula_components', []) \
                                .append('Must be objects with an id '
                                        'and optional order field.')
                            continue

                        component_id = component.get('id')
                        component_title = component.get('title', '')
                        component_sls_path = component.get('sls_path', '')
                        if not any([component_id,
                                   component_title,
                                   component_sls_path]):
                            errors.setdefault(
                                host_string + '.formula_components', []) \
                                .append('Each object in the list must contain '
                                        'an id, title, or sls_path field. An '
                                        'order field may optionally be '
                                        'specified to enforce an ordering '
                                        'of the component provisioning.')
                            continue

                        try:
                            component_order = int(component.get('order', 0))
                            if component_order < 0:
                                errors.setdefault(
                                    host_string + '.formula_components', []) \
                                    .append('Order field must contain a '
                                            'non-negative value.')
                        except ValueError:
                            errors.setdefault(
                                host_string + '.formula_components', []) \
                                .append('Order field must be a non-negative '
                                        'integer.')

                        try:
                            d = {'formula__owner': request.user}
                            if component_id:
                                d['pk'] = component_id
                                component_err = 'an id of {0}'.format(
                                    component_id)
                            elif component_sls_path:
                                d['sls_path__iexact'] = component_sls_path
                                component_err = 'an sls_path of {0}'.format(
                                    component_sls_path
                                )
                            elif component_title:
                                d['title__icontains'] = component_title
                                component_err = '{0} in the title'.format(
                                    component_title
                                )
                            component_objs = FormulaComponent.objects \
                                .filter(**d)
                            if component_objs.count() == 0:
                                errors.setdefault(
                                    host_string + '.formula_components', []) \
                                    .append('Component with {0} does not '
                                            'exist.'.format(component_err))
                            elif component_objs.count() > 1:
                                errors.setdefault(
                                    host_string + '.formula_components', []) \
                                    .append('Multiple components found with '
                                            '{0}.'.format(component_err))

                        except FormulaComponent.DoesNotExist:
                            errors.setdefault(
                                host_string + '.formula_components', []) \
                                .append('Formula component with id {0} does '
                                        'not exist.'.format(component_id))

                # Validating access rules
                if not isinstance(access_rules, list):
                    errors.setdefault(host_string + '.access_rules', []) \
                        .append('Must be a list of access rule objects with '
                                'protocol, from_port, to_port, and rule '
                                'fields')
                for rule_index, rule in enumerate(access_rules):
                    rule_string = host_string + '.access_rules[{0}]' \
                        .format(rule_index)
                    if 'protocol' not in rule:
                        errors.setdefault(rule_string, []).append(
                            'protocol is a required field.'
                        )
                    elif rule['protocol'] not in VALID_PROTOCOLS:
                        errors.setdefault(rule_string, []).append(
                            'protocol {0} is unrecognized. Must be one '
                            'of {1}.'.format(
                                rule['protocol'],
                                ', '.join(VALID_PROTOCOLS)
                            )
                        )
                    if 'from_port' not in rule:
                        errors.setdefault(rule_string, []).append(
                            'from_port is a required field.'
                        )
                    if 'to_port' not in rule:
                        errors.setdefault(rule_string, []).append(
                            'to_port is a required field.'
                        )
                    if 'rule' not in rule:
                        errors.setdefault(rule_string, []).append(
                            'rule is a required field.'
                        )

                # Validating volumes
                for volume_index, volume in enumerate(volumes):
                    volume_string = host_string + '.volumes[{0}]' \
                        .format(volume_index)
                    if 'device' not in volume:
                        errors.setdefault(volume_string, []).append(
                            'device is a required field.'
                        )
                    if 'mount_point' not in volume:
                        errors.setdefault(volume_string, []).append(
                            'mount_point is a required field.'
                        )
                    if 'snapshot' not in volume:
                        errors.setdefault(volume_string, []).append(
                            'snapshot is a required field.'
                        )
                    else:
                        volume['snapshot'] = Snapshot.objects \
                            .get(pk=volume['snapshot'])

                # Validating spot instances
                spot_config = host.get('spot_config', None)
                if spot_config is not None and \
                        not isinstance(spot_config, dict):
                    errors.setdefault(
                        host_string + '.spot_config', []) \
                        .append('Must be a JSON object containing a '
                                'spot_price field.')
                elif spot_config is not None:
                    if 'spot_price' not in spot_config:
                        errors.setdefault(host_string + '.spot_config', []) \
                            .append('spot_price is a required field.')
                    elif not isinstance(spot_config['spot_price'], float):
                        errors.setdefault(host_string + '.spot_config', []) \
                            .append('spot_price must be a decimal value.')
                    elif spot_config['spot_price'] < 0:
                        errors.setdefault(host_string + '.spot_config', []) \
                            .append('spot_price must be a non-negative value.')

        # check component ordering over all hosts
        order_set = set()
        for host in hosts:
            formula_components = host.get('formula_components', [])
            order_set.update([c.get('order', 0)
                              for c in formula_components])

        if sorted(order_set) != range(len(order_set)):
            errors.setdefault('formula_components', []).append(
                'Ordering is zero-based, may have duplicates across hosts, '
                'but can not have any gaps in the order. Your de-duplicated '
                'order: {0}'.format(sorted(order_set)))

        if errors:
            raise BadRequest(errors)

        blueprint = models.Blueprint.objects.create(request.user, request.DATA)
        return Response(self.get_serializer(blueprint).data)


class BlueprintPublicAPIView(generics.ListAPIView):

    model = models.Blueprint
    serializer_class = serializers.BlueprintSerializer

    def get_queryset(self):
        return self.model.objects \
            .filter(public=True) \
            .exclude(owner=self.request.user)


class BlueprintDetailAPIView(PublicBlueprintMixin,
                             generics.RetrieveUpdateDestroyAPIView):
    model = models.Blueprint
    serializer_class = serializers.BlueprintSerializer
    parser_classes = (JSONParser,)

    def update(self, request, *args, **kwargs):
        blueprint = self.get_object()

        # Only the owner of the blueprint can submit PUT/PATCH requests
        if blueprint.owner != request.user:
            raise BadRequest('Only the owner of a blueprint may modify it.')

        # rebuild properties list
        properties = request.DATA.pop('properties', None)
        if properties:
            blueprint.properties = properties

        # since we have already updated the properties list, trick
        # super::update method into thinking no properties have changed
        #request.DATA['properties'] = []
        return super(BlueprintDetailAPIView, self).update(request,
                                                          *args,
                                                          **kwargs)

    def delete(self, request, *args, **kwargs):
        '''
        Override the delete method to check for ownership and prevent
        blueprints from being removed if other resources are using
        them.
        '''
        blueprint = self.get_object()

        # Check ownership
        if blueprint.owner != request.user:
            raise BadRequest('Only the owner of a blueprint may delete it.')

        # Check usage
        stacks = blueprint.stacks.all()
        if stacks:
            stacks = StackSerializer(stacks,
                                     context=dict(request=request)).data
            return Response({
                'detail': 'This blueprint is in use by one or more '
                          'stacks and cannot be removed.',
                'stacks': stacks
            }, status=status.HTTP_400_BAD_REQUEST)

        return super(BlueprintDetailAPIView, self).delete(request,
                                                          *args,
                                                          **kwargs)


class BlueprintPropertiesAPIView(PublicBlueprintMixin,
                                 generics.RetrieveAPIView):
    model = models.Blueprint
    serializer_class = serializers.BlueprintPropertiesSerializer
