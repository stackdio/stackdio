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

import fileinput
import logging
import os
import shutil
import sys
from functools import wraps
from tempfile import mkdtemp

import git
import six
from celery import shared_task
from stackdio.api.formulas.exceptions import FormulaTaskException, InvalidFormula
from stackdio.api.formulas.models import Formula
from stackdio.api.formulas.validators import validate_specfile, validate_component

logger = logging.getLogger(__name__)


def replace_all(rep_file, search_exp, replace_exp):
    for line in fileinput.input(rep_file, inplace=True):
        if search_exp in line:
            line = line.replace(search_exp, replace_exp)
        sys.stdout.write(line)


def get_tmp_repo(formula):
    # temporary directory to clone into so we can read the
    # SPECFILE and do some initial validation
    tmpdir = mkdtemp(prefix='stackdio-')
    reponame = formula.get_repo_name()
    repodir = os.path.join(tmpdir, reponame)

    try:
        # Clone the repo into a temp dir
        return formula.clone_to(repodir)
    except git.GitCommandError:
        raise FormulaTaskException(
            'Unable to clone provided URI. This is either not '
            'a git repository, or you don\'t have permission to clone it.'
        )


def formula_task(*args, **kwargs):
    """
    Create a formula celery task that performs some common functionality and handles errors
    """
    def wrapped(func):

        # Pass the args from stack_task to shared_task
        @shared_task(*args, **kwargs)
        @wraps(func)
        def task(formula_id, *task_args, **task_kwargs):
            try:
                formula = Formula.objects.get(id=formula_id)
            except Formula.DoesNotExist:
                raise ValueError('No formula found with id {}'.format(formula_id))

            try:
                # Call our actual task function and catch some common errors
                return func(formula, *task_args, **task_kwargs)

            except FormulaTaskException as e:
                formula.set_status(Formula.ERROR, six.text_type(e))
                logger.exception(e)
                raise
            except InvalidFormula as e:
                formula.set_status(Formula.ERROR, six.text_type(e))
                logger.exception(e)
                raise
            except Exception as e:
                err_msg = 'Unhandled exception: {}'.format(e)
                formula.set_status(Formula.ERROR, err_msg)
                logger.exception(e)
                raise

        return task

    return wrapped


@formula_task(name='formulas.import_formula')
def import_formula(formula):
    formula.set_status(Formula.IMPORTING, 'Cloning and importing formula.')

    tmp_repo = get_tmp_repo(formula)
    tmp_repo_dir = tmp_repo.working_dir

    # If the main branch fails, don't catch it's exception.
    formula_info = validate_specfile(tmp_repo_dir)

    # update the formula title and description
    formula.title = formula_info.title
    formula.description = formula_info.description
    formula.root_path = formula_info.root_path
    formula.save()

    components = formula_info.components

    # validate components
    for component in components:
        validate_component(tmp_repo_dir, component)

    repos_dir = formula.get_repos_dir()

    # Copy to the HEAD version
    shutil.copytree(tmp_repo_dir, os.path.join(repos_dir, 'HEAD'))

    invalid_versions = []

    for ref in tmp_repo.remote().refs:
        # We don't care about HEAD
        if ref.remote_head == 'HEAD':
            continue

        # Checkout the branch
        try:
            ref.checkout(force=True)
        except TypeError as e:
            # checkout raises a TypeError if you checkout a remote ref :(
            if 'is a detached symbolic reference as it points to' not in e.message:
                raise

        try:
            # Validate the formula
            _, _, _, components = validate_specfile(tmp_repo_dir)
            for component in components:
                validate_component(tmp_repo_dir, component)

        except InvalidFormula:
            # Just add it to the invalid versions, but continue on
            invalid_versions.append(ref.remote_head)
            continue

        version_dir = os.path.join(repos_dir, ref.remote_head)

        # Copy to the new version dir
        shutil.copytree(tmp_repo_dir, version_dir)

    for tag in tmp_repo.tags:
        tmp_repo.git.checkout(tag.name)

        try:
            # Validate the formula
            _, _, _, components = validate_specfile(tmp_repo_dir)
            for component in components:
                validate_component(tmp_repo_dir, component)

        except InvalidFormula:
            # Just add it to the invalid versions, but continue on
            invalid_versions.append(tag.name)
            continue

        version_dir = os.path.join(repos_dir, tag.name)

        # Copy to the new version dir
        shutil.copytree(tmp_repo_dir, version_dir)

    tmpdir = os.path.dirname(tmp_repo_dir)

    # remove tmpdir now that we're finished
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)

    if invalid_versions:
        status_msg = ('Import complete. Formula is ready, but the following '
                      'versions were not valid: {}'.format(', '.join(invalid_versions)))
    else:
        status_msg = 'Import complete. Formula is now ready to be used.'

    formula.set_status(Formula.COMPLETE, status_msg)

    return True


@formula_task(name='formulas.update_formula')
def update_formula(formula, version=None):
    formula.set_status(Formula.IMPORTING, 'Updating formula.')

    repo = formula.get_repo(version)

    if repo is None:
        raise FormulaTaskException('Could not find the repo.  Formula never got cloned.')

    repo_dir = repo.working_dir

    # Save the current commit
    old_commit = repo.head.commit

    try:
        # Do a fetch first
        repo.remote().fetch(prune=True)

        # Then checkout the remote branch
        try:
            repo.remote().refs[version].checkout()
        except TypeError as e:
            # checkout raises a TypeError if you checkout a remote ref :(
            if 'is a detached symbolic reference as it points to' not in e.message:
                raise

        # Grab the new commit
        new_commit = repo.head.commit

        # If nothing changed, we're good
        if new_commit == old_commit:
            formula.set_status(Formula.COMPLETE, 'There were no changes to the repository.')
            return True

        formula_info = validate_specfile(repo_dir)

        components = formula_info.components

        # Validate all the new components
        for component in components:
            validate_component(repo_dir, component)

        # Everything was validated, update the database
        formula.title = formula_info.title
        formula.description = formula_info.description
        formula.root_path = formula_info.root_path
        formula.save()

        formula.set_status(Formula.COMPLETE,
                           'Import complete. Formula is now ready to be used.')

        return True

    except Exception:
        # Roll back the pull
        repo.git.reset('--hard', old_commit)
        raise
