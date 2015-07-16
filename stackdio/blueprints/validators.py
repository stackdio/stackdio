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


import string

from . import models
from cloud.models import Snapshot
from core.validation import ValidationErrors, BaseValidator

VAR_NAMESPACE = 'namespace'
VAR_USERNAME = 'username'
VAR_INDEX = 'index'
VALID_PROTOCOLS = ('tcp', 'udp', 'icmp')
VALID_TEMPLATE_VARS = (VAR_NAMESPACE, VAR_USERNAME, VAR_INDEX)


class BlueprintValidator(BaseValidator):

    def validate(self):
        self._validate_title()
        self._validate_description()
        self._validate_public()
        self._validate_properties()
        self._validate_hosts()
        self._validate_component_ordering()

        return self._errors

    def _validate_title(self):
        title = self.data.get('title', '')
        if not title:
            self.set_error('title', ValidationErrors.REQUIRED_FIELD)
            return False

        # check for duplicates
        elif models.Blueprint.objects.filter(title=title).count():
            self.set_error('title', ValidationErrors.DUP_BLUEPRINT)
            return False
        return True

    def _validate_description(self):
        description = self.data.get('description', '')
        if not description:
            self.set_error('description', ValidationErrors.REQUIRED_FIELD)
            return False
        return True

    def _validate_public(self):
        public = self.data.get('public', False)
        if not isinstance(public, bool):
            self.set_error('public', ValidationErrors.BOOLEAN_REQUIRED)
            return False
        return True

    def _validate_properties(self):
        properties = self.data.get('properties', {})
        if not isinstance(properties, dict):
            self.set_error('properties', ValidationErrors.OBJECT_REQUIRED)
            return False
        else:
            # user properties are not allowed to provide a __stackdio__ key
            if '__stackdio__' in properties:
                self.set_error('properties',
                               ValidationErrors.STACKDIO_RESTRICTED_KEY)
            return False
        return True

    def _validate_hosts(self):
        self._host_titles = set()

        hosts = self.data.get('hosts', [])
        if not isinstance(hosts, list):
            self.set_error('hosts', ValidationErrors.LIST_REQUIRED)
            return False
        elif len(hosts) == 0:
            self.set_error('hosts', ValidationErrors.MIN_HOSTS)
            return False

        for host_index, host in enumerate(hosts):
            if not isinstance(host, dict):
                self._errors.setdefault('hosts', []).append(
                    ValidationErrors.OBJECT_REQUIRED
                )
                continue

            host_errors = {}
            host_errors.update(self._validate_host_title(host))
            host_errors.update(self._validate_host_description(host))
            host_errors.update(self._validate_count(host))
            host_errors.update(self._validate_host_size(host))
            host_errors.update(self._validate_host_template(host))
            profile_error = self._validate_host_profile(host)
            host_errors.update(profile_error)

            if not profile_error:
                cloud_profile = models.CloudProfile.objects.get(
                    pk=host['cloud_profile']
                )
                if not cloud_profile.cloud_account.vpc_enabled:
                    host_errors.update(self._validate_host_zone(host))
                else:
                    host_errors.update(self._validate_host_subnet(host))

            host_errors.update(self._validate_host_components(host))
            host_errors.update(self._validate_host_access_rules(host))
            host_errors.update(self._validate_host_volumes(host))
            host_errors.update(self._validate_host_spot_config(host))

            self._errors.setdefault('hosts', []).append(host_errors)

        if not any(self._errors['hosts']):
            del self._errors['hosts']

    def _validate_host_title(self, host):
        e = {}
        if 'title' not in host:
            e['title'] = ValidationErrors.REQUIRED_FIELD
        elif not host['title']:
            e['title'] = ValidationErrors.REQUIRED_FIELD
        elif host['title'] in self._host_titles:
            e['title'] = ValidationErrors.DUP_HOST_TITLE
        else:
            self._host_titles.add(host['title'])
        return e

    def _validate_host_description(self, host):
        e = {}
        if 'description' not in host or not host['description']:
            e['description'] = ValidationErrors.REQUIRED_FIELD
        return e

    def _validate_host_size(self, host):
        e = {}
        if 'size' not in host:
            e['size'] = ValidationErrors.REQUIRED_FIELD
        elif not isinstance(host['size'], int):
            e['size'] = ValidationErrors.INT_REQUIRED
        # check the size instance
        else:
            try:
                models.CloudInstanceSize.objects.get(pk=host['size'])
            except models.CloudInstanceSize.DoesNotExist:
                e['size'] = ValidationErrors.DOES_NOT_EXIST
        return e

    def _validate_host_template(self, host):
        e = {}
        k = 'hostname_template'
        if k not in host:
            e[k] = ValidationErrors.REQUIRED_FIELD
        else:
            # check for valid hostname_template variables
            f = string.Formatter()
            v = [x[1] for x in f.parse(
                host[k]
            ) if x[1]]
            invalid_vars = [x for x in v
                            if x not in VALID_TEMPLATE_VARS]

            if invalid_vars:
                e.setdefault(k, []).append(
                    'Invalid variables: {0}'.format(', '.join(invalid_vars))
                )

            # VAR_INDEX must be present if host count is greater than
            # one
            if host.get('count', 0) > 1 and VAR_INDEX not in v:
                e.setdefault(k, []).append(
                    'The variable {0} must be used when a host count is '
                    'greater than one.'.format(VAR_INDEX)
                )

            # check for underscores and hyphens on the beginning/end
            if '_' in host[k]:
                e.setdefault(k, []).append(
                    'Underscores are not allowed in templates.'
                )
            if host[k].startswith('-') or host[k].endswith('-'):
                e.setdefault(k, []).append(
                    'Hyphens on the beginning or end of the '
                    'template is not allowed.'
                )
        return e

    def _validate_host_profile(self, host):
        e = {}
        if 'cloud_profile' not in host:
            e['cloud_profile'] = ValidationErrors.REQUIRED_FIELD
        elif not isinstance(host['cloud_profile'], int):
            e['cloud_profile'] = ValidationErrors.INT_REQUIRED
        # check the cloud profile instance
        else:
            try:
                models.CloudProfile.objects.get(
                    pk=host['cloud_profile']
                )
            except models.CloudProfile.DoesNotExist:
                e['cloud_profile'] = ValidationErrors.DOES_NOT_EXIST
        return e

    def _validate_host_zone(self, host):
        e = {}
        # Availability zone is for EC2 Classic mode, while subnet is
        # with EC2 VPC mode
        if 'zone' not in host:
            e['zone'] = ValidationErrors.REQUIRED_FIELD
        elif not isinstance(host['zone'], int):
            e['zone'] = ValidationErrors.INT_REQUIRED
        # check the zone instance
        else:
            try:
                models.CloudZone.objects.get(pk=host['zone'])
            except models.CloudZone.DoesNotExist:
                e['zone'] = ValidationErrors.DOES_NOT_EXIST
        return e

    def _validate_host_subnet(self, host):
        e = {}
        # Subnets are for hosts being launched into an account that's using
        # VPC
        if 'subnet_id' not in host:
            e['subnet_id'] = ValidationErrors.REQUIRED_FIELD
        # check for the zone
        else:
            try:
                cloud_profile = models.CloudProfile.objects.get(
                    pk=host['cloud_profile']
                )
                driver = cloud_profile.get_driver()
                subnets = driver.get_vpc_subnets([host['subnet_id']])
                if subnets is None:
                    e['subnet_id'] = ValidationErrors.DOES_NOT_EXIST
            except Exception:
                e['subnet_id'] = ValidationErrors.UNHANDLED_ERROR
        return e

    def _validate_host_components(self, host):
        e = {}
        formula_components = host.get('formula_components', [])
        if not isinstance(formula_components, list):
            e['formula_components'] = ValidationErrors.LIST_REQUIRED
        else:
            for component in formula_components:
                if not isinstance(component, dict):
                    e.setdefault('formula_components', []).append(
                        ValidationErrors.OBJECT_REQUIRED
                    )
                    continue

                component_id = component.get('id')
                component_title = component.get('title', '')
                component_sls_path = component.get('sls_path', '')
                if not any([component_id,
                            component_title,
                            component_sls_path]):
                    e.setdefault('formula_components', []).append(
                        'Each object in the list must contain an id, title, '
                        'or sls_path field. An order field may optionally be '
                        'specified to enforce an ordering of the component '
                        'provisioning.'
                    )
                    continue

                errors = {}
                errors.update(self._validate_component(component))
                errors.update(self._validate_component_order(component))

                e.setdefault('formula_components', []).append(errors)

        if not any(e.get('formula_components', [])):
            return {}
        return e

    def _validate_component(self, component):
        e = {}
        component_id = component.get('id')
        component_title = component.get('title', '')
        component_sls_path = component.get('sls_path', '')

        kwargs = {}
        if component_id:
            k = 'id'
            kwargs['pk'] = component_id
        elif component_sls_path:
            k = 'sls_path'
            kwargs['sls_path__iexact'] = component_sls_path
        elif component_title:
            k = 'title'
            kwargs['title__icontains'] = component_title
        component_objs = models.FormulaComponent.objects.filter(**kwargs)
        if component_objs.count() == 0:
            e[k] = ValidationErrors.DOES_NOT_EXIST
        elif component_objs.count() > 1:
            e[k] = ValidationErrors.MULTIPLE_COMPONENTS

        return e

    def _validate_component_order(self, component):
        e = {}
        try:
            component_order = int(component.get('order', 0) or 0)
            if component_order < 0:
                e['order'] = ValidationErrors.INT_REQUIRED
        except (TypeError, ValueError):
            e['order'] = ValidationErrors.INVALID_INT
        return e

    def _validate_host_access_rules(self, host):
        e = {}
        access_rules = host.get('access_rules', [])
        if not isinstance(access_rules, list):
            e['access_rules'] = ValidationErrors.LIST_REQUIRED
        else:
            for rule in access_rules:
                if not isinstance(rule, dict):
                    e.setdefault('access_rules', []).append(
                        ValidationErrors.OBJECT_REQUIRED
                    )
                    continue

                errors = {}
                errors.update(self._validate_access_rule_protocol(rule))
                errors.update(self._validate_access_rule_ports(rule))

                if 'rule' not in rule:
                    errors['rule'] = ValidationErrors.REQUIRED_FIELD

                e.setdefault('access_rules', []).append(errors)

        if not any(e.get('access_rules', [])):
            return {}
        return e

    def _validate_access_rule_protocol(self, rule):
        e = {}
        if 'protocol' not in rule:
            e['protocol'] = ValidationErrors.REQUIRED_FIELD
        elif rule['protocol'] not in VALID_PROTOCOLS:
            e['protocol'] = 'Invalid protocol. Must be one of {0}.'.format(
                ', '.join(VALID_PROTOCOLS)
            )
        return e

    def _validate_access_rule_ports(self, rule):
        e = {}
        for k in ('from_port', 'to_port'):
            if k not in rule:
                e[k] = ValidationErrors.REQUIRED_FIELD
            elif not isinstance(rule[k], int):
                e[k] = ValidationErrors.INT_REQUIRED
            elif rule[k] < 0 or rule[k] > 65535:
                e[k] = 'Must be in the range 0-65535.'

        if e:
            return e

        if rule['from_port'] > rule['to_port']:
            e['from_port'] = 'Must be less than to_port value.'

        return e

    def _validate_host_volumes(self, host):
        e = {}
        volumes = host.get('volumes', [])
        if not isinstance(volumes, list):
            e['volumes'] = ValidationErrors.LIST_REQUIRED
        else:
            for volume in volumes:
                if not isinstance(volume, dict):
                    e.setdefault('volumes', []).append(
                        ValidationErrors.OBJECT_REQUIRED
                    )
                    continue

                errors = {}
                errors.update(self._validate_host_volume_device(volume))
                errors.update(self._validate_host_volume_mount_point(volume))
                errors.update(self._validate_host_volume_snapshot(volume))
                e.setdefault('volumes', []).append(errors)

        if not any(e.get('volumes', [])):
            return {}
        return e

    def _validate_host_volume_device(self, volume):
        e = {}
        if 'device' not in volume:
            e['device'] = ValidationErrors.REQUIRED_FIELD
        return e

    def _validate_host_volume_mount_point(self, volume):
        e = {}
        if 'mount_point' not in volume:
            e['mount_point'] = ValidationErrors.REQUIRED_FIELD
        return e

    def _validate_host_volume_snapshot(self, volume):
        e = {}
        if 'snapshot' not in volume:
            e['snapshot'] = ValidationErrors.REQUIRED_FIELD
        elif not isinstance(volume['snapshot'], int):
            e['snapshot'] = ValidationErrors.INT_REQUIRED
        else:
            try:
                Snapshot.objects.get(pk=volume['snapshot'])
            except Snapshot.DoesNotExist:
                e['snapshot'] = ValidationErrors.DOES_NOT_EXIST
        return e

    def _validate_host_spot_config(self, host):
        e = {}

        spot_config = host.get('spot_config', None)
        if spot_config is not None and not isinstance(spot_config, dict):
            e['spot_config'] = ValidationErrors.OBJECT_REQUIRED
        elif spot_config is not None:
            errors = {}
            if 'spot_price' not in spot_config:
                errors['spot_price'] = ValidationErrors.REQUIRED_FIELD
            elif not isinstance(spot_config['spot_price'], float):
                errors['spot_price'] = ValidationErrors.DECIMAL_REQUIRED
            elif spot_config['spot_price'] < 0:
                errors['spot_price'] = ValidationErrors.DECIMAL_REQUIRED

            if errors:
                e.setdefault('spot_config', []).append(errors)

        return e

    def _validate_component_ordering(self):
        order_set = set()
        hosts = self.data.get('hosts', [])
        for host in hosts:
            components = host.get('formula_components', [])
            order_set.update([c.get('order', 0) or 0 for c in components])

        if sorted(order_set) != range(len(order_set)):
            self.set_error(
                'formula_components',
                'Ordering is zero-based, may have duplicates across hosts, '
                'but can not have any gaps in the order. Your de-duplicated '
                'order: {0}'.format(sorted(order_set))
            )
