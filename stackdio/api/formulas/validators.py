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

import os

import yaml
from rest_framework.serializers import ValidationError


def validate_specfile(formula, repodir):
    from .tasks import FormulaTaskException
    specfile_path = os.path.join(repodir, 'SPECFILE')
    if not os.path.isfile(specfile_path):
        raise FormulaTaskException(
            formula,
            'Formula did not have a SPECFILE. Each formula must define a '
            'SPECFILE in the root of the repository.')

    # Load and validate the SPECFILE
    with open(specfile_path) as f:
        specfile = yaml.safe_load(f)

    formula_title = specfile.get('title', '')
    formula_description = specfile.get('description', '')
    root_path = specfile.get('root_path', '')
    components = specfile.get('components', [])

    if not formula_title:
        raise FormulaTaskException(
            formula,
            "Formula SPECFILE 'title' field is required.")

    if not root_path:
        raise FormulaTaskException(
            formula,
            "Formula SPECFILE 'root_path' field is required.")

    # check root path location
    if not os.path.isdir(os.path.join(repodir, root_path)):
        raise FormulaTaskException(
            formula,
            'Formula SPECFILE \'root_path\' must exist in the formula. '
            'Unable to locate directory: {0}'.format(root_path))

    if not components:
        raise FormulaTaskException(
            formula,
            'Formula SPECFILE \'components\' field must be a non-empty '
            'list of components.')

    # Give back the components
    return formula_title, formula_description, root_path, components


def validate_component(formula, repodir, component):
    from .tasks import FormulaTaskException
    # check for required fields
    if 'title' not in component or 'sls_path' not in component:
        raise FormulaTaskException(
            formula,
            'Each component in the SPECFILE must contain a \'title\' '
            'and \'sls_path\' field.')

    # determine if the sls_path is valid...we're looking for either
    # a directory with an init.sls or an sls file of the same name
    # as the last location of the path
    component_title = component['title']
    sls_path = component['sls_path'].replace('.', '/')
    init_file = os.path.join(sls_path, 'init.sls')
    sls_file = sls_path + '.sls'
    abs_init_file = os.path.join(repodir, init_file)
    abs_sls_file = os.path.join(repodir, sls_file)

    if not os.path.isfile(abs_init_file) and \
            not os.path.isfile(abs_sls_file):
        raise FormulaTaskException(
            formula,
            'Could not locate an SLS file for component \'{0}\'. '
            'Expected to find either \'{1}\' or \'{2}\'.'.format(component_title,
                                                                 init_file,
                                                                 sls_file)
        )


def validate_formula_components(components, versions):
    version_map = {}

    # Build the map of formula -> version
    for version in versions:
        version_map[version['formula']] = version['version']

    errors = {}

    for component in components:
        formula = component.get('formula')
        if formula is not None:
            # We only care to validate here if there is a formula in the component.
            sls_path = component['sls_path']

            version = version_map.get(formula)

            component_list = formula.components_for_version(version)

            if sls_path not in component_list:
                err_msg = 'formula `{0}` does not contain an sls_path called `{1}`.'
                errors.setdefault('sls_path', []).append(err_msg.format(formula.uri, sls_path))

    if errors:
        raise ValidationError(errors)

    return components
