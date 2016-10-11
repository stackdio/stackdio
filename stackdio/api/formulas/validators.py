# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
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

from __future__ import unicode_literals

import collections
import os

import yaml
from django.core.validators import URLValidator
from django.utils.translation import ugettext_lazy as _
from rest_framework.serializers import CharField, ValidationError

from stackdio.api.formulas.exceptions import InvalidFormula, InvalidFormulaComponent


FormulaInfo = collections.namedtuple('FormulaInfo',
                                     ['title', 'description', 'root_path', 'components'])


class FormulaURLValidator(URLValidator):
    # Use the valid git url schemes
    schemes = ['ssh', 'git', 'git+ssh', 'http', 'https', 'ftp', 'ftps', 'rsync']
    message = _('Enter a valid git URL.')


class FormulaURLField(CharField):
    default_error_messages = {
        'invalid': _('Enter a valid git URL.')
    }

    def __init__(self, **kwargs):
        super(FormulaURLField, self).__init__(**kwargs)
        validator = FormulaURLValidator(message=self.error_messages['invalid'])
        self.validators.append(validator)


def validate_specfile(repodir):
    specfile_path = os.path.join(repodir, 'SPECFILE')
    if not os.path.isfile(specfile_path):
        raise InvalidFormula(
            'Formula did not have a SPECFILE. Each formula must define a '
            'SPECFILE in the root of the repository.'
        )

    # Load and validate the SPECFILE
    with open(specfile_path) as f:
        specfile = yaml.safe_load(f)

    formula_title = specfile.get('title', '')
    formula_description = specfile.get('description', '')
    root_path = specfile.get('root_path', '')
    components = specfile.get('components', [])

    if not formula_title:
        raise InvalidFormula('Formula SPECFILE \'title\' field is required.')

    if not root_path:
        raise InvalidFormula('Formula SPECFILE \'root_path\' field is required.')

    # check root path location
    if not os.path.isdir(os.path.join(repodir, root_path)):
        raise InvalidFormula(
            'Formula SPECFILE \'root_path\' must exist in the formula. '
            'Unable to locate directory: {0}'.format(root_path)
        )

    if not components:
        raise InvalidFormula(
            'Formula SPECFILE \'components\' field must be a non-empty '
            'list of components.'
        )

    # Give back the components
    return FormulaInfo(formula_title, formula_description, root_path, components)


def validate_component(repodir, component):
    # check for required fields
    if 'title' not in component or 'sls_path' not in component:
        raise InvalidFormulaComponent(
            'Each component in the SPECFILE must contain a \'title\' '
            'and \'sls_path\' field.'
        )

    # determine if the sls_path is valid...we're looking for either
    # a directory with an init.sls or an sls file of the same name
    # as the last location of the path
    component_title = component['title']
    sls_path = component['sls_path'].replace('.', '/')
    init_file = os.path.join(sls_path, 'init.sls')
    sls_file = sls_path + '.sls'
    abs_init_file = os.path.join(repodir, init_file)
    abs_sls_file = os.path.join(repodir, sls_file)

    err_msg = ('Could not locate an SLS file for component \'{0}\'. Expected to find either '
               '\'{1}\' or \'{2}\'.'.format(component_title, init_file, sls_file))

    if not os.path.isfile(abs_init_file) and not os.path.isfile(abs_sls_file):
        raise InvalidFormulaComponent(err_msg)


def validate_formula_components(components, versions):
    """
    Validate a LIST of formula components, where the versions DO NOT already exist
    i.e. creating a blueprint
    """
    version_map = {}

    # Build the map of formula -> version
    for version in versions:
        version_map[version['formula']] = version['version']

    errors = {}

    for component in components:
        validated = component.pop('validated', False)
        formula = component.get('formula')
        if not validated:
            # We only care to validate here it wasn't already validated in the other serializer.
            sls_path = component['sls_path']

            version = version_map.get(formula)

            component_list = formula.components(version)

            if sls_path not in component_list:
                err_msg = 'formula `{0}` does not contain an sls_path called `{1}`.'
                errors.setdefault('sls_path', []).append(err_msg.format(formula.uri, sls_path))

    if errors:
        raise ValidationError(errors)

    return components


def validate_formula_component(component, versions=()):
    """
    Validate a SINGLE formula component from versions that already exist.
    i.e. adding a formula component to a blueprint or cloud account
    """
    version_map = {}

    # Build the map of formula -> version
    for version in versions:
        version_map[version.formula] = version.version

    errors = {}

    formula = component.get('formula')
    sls_path = component['sls_path']
    version = version_map.get(formula, formula.default_version)
    component_list = formula.components(version)

    if sls_path not in component_list:
        err_msg = 'formula `{0}` does not contain an sls_path called `{1}`.'
        errors.setdefault('sls_path', []).append(err_msg.format(formula.uri, sls_path))

    if errors:
        raise ValidationError(errors)

    return component
