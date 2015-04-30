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


import logging
import os
import shutil
import fileinput
import sys
from tempfile import mkdtemp
from urlparse import urlsplit, urlunsplit

import celery
import yaml
import git

from formulas.models import Formula


logger = logging.getLogger(__name__)


class FormulaTaskException(Exception):
    def __init__(self, formula, error):
        formula.set_status(Formula.ERROR, error)
        super(FormulaTaskException, self).__init__(error)


def replace_all(file, searchExp, replaceExp):
    for line in fileinput.input(file, inplace=True):
        if searchExp in line:
            line = line.replace(searchExp, replaceExp)
        sys.stdout.write(line)


def clone_to_temp(formula, git_password):

    # temporary directory to clone into so we can read the
    # SPECFILE and do some initial validation
    tmpdir = mkdtemp(prefix='stackdio-')
    reponame = formula.get_repo_name()
    repodir = os.path.join(tmpdir, reponame)

    uri = formula.uri
    # Add the password for a private repo
    if formula.private_git_repo:
        parsed = urlsplit(uri)
        hostname = parsed.netloc.split('@')[1]
        uri = urlunsplit((
            parsed.scheme,
            '{0}:{1}@{2}'.format(
                formula.git_username, git_password, hostname),
            parsed.path,
            parsed.query,
            parsed.fragment
        ))

    try:
        # Clone the repo into a temp dir
        repo = git.Repo.clone_from(uri, repodir)

        origin = repo.remotes.origin.name

        # Remove the password from the config
        repo.git.remote('set-url', origin, formula.uri)

        # Remove the logs which also store the password
        log_dir = os.path.join(repodir, '.git', 'logs')
        # if os.path.isdir(log_dir):
        shutil.rmtree(log_dir)

    except git.GitCommandError:
        raise FormulaTaskException(
            formula,
            'Unable to clone provided URI. This is either not '
            'a git repository, or you don\'t have permission to clone it.  '
            'Note that private repositories require the https protocol.')

    # return the path where the repo is
    return repodir


def validate_specfile(formula, repodir):

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
            'Expected to find either \'{1}\' or \'{2}\'.'
            .format(component_title, init_file, sls_file))


# TODO: Ignoring complexity issues
@celery.task(name='formulas.import_formula')  # NOQA
def import_formula(formula_id, git_password):
    try:
        formula = Formula.objects.get(pk=formula_id)
        formula.set_status(Formula.IMPORTING, 'Cloning and importing formula.')

        repodir = clone_to_temp(formula, git_password)

        root_dir = formula.get_repo_dir()

        if os.path.isdir(root_dir):
            raise FormulaTaskException(
                formula,
                'Formula root path already exists.')

        formula_title, formula_description, root_path, components = validate_specfile(formula, repodir)

        # update the formula title and description
        formula.title = formula_title
        formula.description = formula_description
        formula.root_path = root_path
        formula.save()

        # validate components
        for component in components:
            validate_component(formula, repodir, component)

        # all seems to be fine with the structure and mapping of the SPECFILE,
        # so now we'll build out the individual components of the formula
        # according to the SPECFILE
        for component in components:
            title = component['title']
            description = component.get('description', '')
            sls_path = component['sls_path']
            formula.components.create(title=title,
                                      sls_path=sls_path,
                                      description=description)

        root_dir = formula.get_repo_dir()

        # move the cloned formula repository to a location known by salt
        # so we can start using the states in this formula
        shutil.move(repodir, root_dir)

        tmpdir = os.path.dirname(repodir)

        # remove tmpdir now that we're finished
        if os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir)

        formula.set_status(Formula.COMPLETE,
                           'Import complete. Formula is now ready to be used.')

        return True
    except Exception, e:
        if isinstance(e, FormulaTaskException):
            raise
        logger.exception(e)
        raise FormulaTaskException(formula, 'An unhandled exception occurred.')


# TODO: Ignoring complexity issues
@celery.task(name='formulas.update_formula')  # NOQA
def update_formula(formula_id, git_password):
    repo = None
    current_commit = None
    try:
        formula = Formula.objects.get(pk=formula_id)
        formula.set_status(Formula.IMPORTING, 'Updating formula.')

        repodir = formula.get_repo_dir()

        repo = git.Repo(repodir)

        current_commit = repo.head.commit

        origin = repo.remotes.origin.name

        # Add the password for a private repo
        if formula.private_git_repo:
            parsed = urlsplit(formula.uri)
            hostname = parsed.netloc.split('@')[1]
            uri = urlunsplit((
                parsed.scheme,
                '{0}:{1}@{2}'.format(
                    formula.git_username, git_password, hostname),
                parsed.path,
                parsed.query,
                parsed.fragment
            ))

            # add the password to the config
            repo.git.remote('set-url', origin, uri)

        result = repo.remotes.origin.pull()
        if len(result) == 1 and result[0].commit == current_commit:
            formula.set_status(Formula.COMPLETE,
                               'There were no changes to the repository.')
            return True

        if formula.private_git_repo:
            # remove the password from the config
            repo.git.remote('set-url', origin, formula.uri)

            # Remove the logs which also store the password
            log_dir = os.path.join(repodir, '.git', 'logs')
            if os.path.isdir(log_dir):
                shutil.rmtree(log_dir)

        formula_title, formula_description, root_path, components = validate_specfile(formula, repodir)

        old_components = formula.components.all()

        # Check for added or changed components
        added_components = []
        changed_components = []
        removed_components = []

        for component in components:

            # Check to see if the component was already in the formula
            exists = False
            for old_component in old_components:
                if component['sls_path'] == old_component.sls_path:
                    # If we find a matching sls path,
                    # update the associated title and description
                    changed_components.append(component)
                    exists = True
                    break

            # if not, set it to be added
            if not exists:
                added_components.append(component)

        # Check for removed components
        for old_component in old_components:

            # check if the old component is in the new formula
            exists = False
            for component in components:
                if component['sls_path'] == old_component.sls_path:
                    exists = True
                    break

            if not exists:
                removed_components.append(old_component)

        # Everything was validated, update the database
        formula.title = formula_title
        formula.description = formula_description
        formula.root_path = root_path
        formula.save()

        # validate new components
        for component in added_components:
            validate_component(formula, repodir, component)

        # validate changed components
        for component in changed_components:
            validate_component(formula, repodir, component)

        # Check to see if the removed components are used
        removal_errors = []
        for component in removed_components:
            blueprint_hosts = component.blueprinthostformulacomponent_set.all()
            if len(blueprint_hosts) is 0:
                component.delete()
            else:
                removal_errors.append(component.sls_path)

        if len(removal_errors) != 0:
            errors = ', '.join(removal_errors)
            formula.set_status(
                Formula.COMPLETE,
                'Formula could not be updated.  The following components '
                'are used in blueprints: {0}.   '
                'Your formula was left unchanged.'.format(errors))
            # Roll back the pull
            repo.git.reset('--hard', current_commit)
            return False

        # Add the new components
        for component in added_components:
            title = component['title']
            description = component.get('description', '')
            sls_path = component['sls_path']
            formula.components.create(title=title,
                                      sls_path=sls_path,
                                      description=description)

        # Update the other components
        for component in changed_components:
            sls_path = component['sls_path']
            to_change = formula.components.get(sls_path=sls_path)
            to_change.title = component['title']
            to_change.description = component.get('description', '')
            to_change.save()

        formula.set_status(Formula.COMPLETE,
                           'Import complete. Formula is now ready to be used.')

        return True

    except Exception, e:
        # Roll back the pull
        if repo is not None and current_commit is not None:
            repo.git.reset('--hard', current_commit)
        if isinstance(e, FormulaTaskException):
            raise FormulaTaskException(
                formula,
                e.message + ' Your formula was not changed.')
        logger.exception(e)
        raise FormulaTaskException(
            formula,
            'An unhandled exception occurred.  Your formula was not changed')
