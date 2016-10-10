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


import fileinput
import logging
import os
import shutil
import sys
from tempfile import mkdtemp

import git
from celery import shared_task
from six.moves.urllib_parse import urlsplit, urlunsplit  # pylint: disable=import-error

from stackdio.api.formulas.validators import validate_specfile, validate_component
from .models import Formula

logger = logging.getLogger(__name__)


class FormulaTaskException(Exception):
    def __init__(self, formula, error):
        formula.set_status(Formula.ERROR, error)
        super(FormulaTaskException, self).__init__(error)


def replace_all(rep_file, search_exp, replace_exp):
    for line in fileinput.input(rep_file, inplace=True):
        if search_exp in line:
            line = line.replace(search_exp, replace_exp)
        sys.stdout.write(line)


def clone_to_temp(formula):
    # temporary directory to clone into so we can read the
    # SPECFILE and do some initial validation
    tmpdir = mkdtemp(prefix='stackdio-')
    reponame = formula.get_repo_name()
    repodir = os.path.join(tmpdir, reponame)

    try:
        # Clone the repo into a temp dir
        git.Repo.clone_from(formula.uri, repodir)
    except git.GitCommandError:
        raise FormulaTaskException(
            formula,
            'Unable to clone provided URI. This is either not '
            'a git repository, or you don\'t have permission to clone it.'
        )

    # return the path where the repo is
    return repodir


@shared_task(name='formulas.import_formula')
def import_formula(formula_id):
    formula = None
    try:
        formula = Formula.objects.get(id=formula_id)
        formula.set_status(Formula.IMPORTING, 'Cloning and importing formula.')

        repodir = clone_to_temp(formula)

        root_dir = formula.get_repos_dir()

        if os.path.isdir(root_dir):
            raise FormulaTaskException(
                formula,
                'Formula root path already exists.'
            )

        formula_title, formula_description, root_path, components = validate_specfile(formula,
                                                                                      repodir)

        # update the formula title and description
        formula.title = formula_title
        formula.description = formula_description
        formula.root_path = root_path
        formula.save()

        # validate components
        for component in components:
            validate_component(formula, repodir, component)

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
    except FormulaTaskException:
        raise
    except Exception as e:
        logger.exception(e)
        raise FormulaTaskException(formula, 'An unhandled exception occurred.')


# TODO: Ignoring complexity issues
@shared_task(name='formulas.update_formula')
def update_formula(formula_id, version, repodir=None, raise_exception=True):
    repo = None
    current_commit = None
    formula = None
    origin = None

    try:
        formula = Formula.objects.get(pk=formula_id)
        formula.set_status(Formula.IMPORTING, 'Updating formula.')

        if repodir is None:
            repodir = formula.get_repo_dir()
            repo = formula.repo
        else:
            repo = git.Repo(repodir)

        # Ensure that the proper version is active
        repo.git.checkout(version)

        current_commit = repo.head.commit

        origin = repo.remotes.origin.name

        result = repo.remotes.origin.pull()
        if len(result) == 1 and result[0].commit == current_commit:
            formula.set_status(Formula.COMPLETE,
                               'There were no changes to the repository.')
            return True

        formula_title, formula_description, root_path, components = validate_specfile(formula,
                                                                                      repodir)

        # Validate all the new components
        for component in components:
            validate_component(formula, repodir, component)

        # Everything was validated, update the database
        formula.title = formula_title
        formula.description = formula_description
        formula.root_path = root_path
        formula.save()

        formula.set_status(Formula.COMPLETE,
                           'Import complete. Formula is now ready to be used.')

        return True

    except Exception as e:
        # Roll back the pull
        if repo is not None and current_commit is not None:
            repo.git.reset('--hard', current_commit)
        if isinstance(e, FormulaTaskException):
            if raise_exception:
                raise FormulaTaskException(
                    formula,
                    e.message + ' Your formula was not changed.'
                )
        logger.warning(e)
        if raise_exception:
            raise FormulaTaskException(
                formula,
                'An unhandled exception occurred.  Your formula was not changed'
            )
