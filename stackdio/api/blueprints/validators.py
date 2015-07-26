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

import re
import string

from rest_framework.serializers import ValidationError

from stackdio.core.validators import BaseValidator

VAR_NAMESPACE = 'namespace'
VAR_USERNAME = 'username'
VAR_INDEX = 'index'
VALID_PROTOCOLS = ('tcp', 'udp', 'icmp')
VALID_TEMPLATE_VARS = (VAR_NAMESPACE, VAR_USERNAME, VAR_INDEX)

# This DOES NOT enforce that hostnames must not end with hyphens, we'll do that manually
HOSTNAME_TEMPLATE_REGEX = r'[a-z0-9\-]+'


class BlueprintHostnameTemplateValidator(BaseValidator):

    def validate(self, value):
        # check for valid hostname_template variables
        formatter = string.Formatter()
        template_vars = [x[1] for x in formatter.parse(value) if x[1]]

        invalid_vars = []
        for var in template_vars:
            if var not in VALID_TEMPLATE_VARS:
                invalid_vars.append(var)

        errors = []

        if invalid_vars:
            errors.append('Invalid variables: {0}'.format(', '.join(invalid_vars)))

        raw_str = ''.join([x[0] for x in formatter.parse(value)])

        if not re.match(HOSTNAME_TEMPLATE_REGEX, raw_str):
            errors.append('May only contain lowercase letters, numbers, and hyphens.')

        if raw_str[0] == '-' or raw_str[-1] == '-':
            errors.append('May not start or end with a hyphen.')

        if errors:
            raise ValidationError({
                'hostname_template': errors
            })
