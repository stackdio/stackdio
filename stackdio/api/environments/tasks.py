# -*- coding: utf-8 -*-

# Copyright 2017,  Digital Reasoning
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

import logging
from functools import wraps

import salt.client
import six
from celery import shared_task
from django.conf import settings
from stackdio.api.environments import utils
from stackdio.api.environments.exceptions import EnvironmentTaskException
from stackdio.api.environments.models import Environment
from stackdio.core.constants import Activity, ComponentStatus
from stackdio.core.utils import auto_retry
from stackdio.salt.utils.client import (
    StackdioLocalClient,
    StackdioRunnerClient,
    StackdioSaltClientException,
)

logger = logging.getLogger(__name__)


def environment_task(*args, **kwargs):
    """
    Create an environment celery task that performs some common functionality and handles errors
    """
    final_task = kwargs.pop('final_task', False)

    def wrapped(func):

        # Pass the args from environment_task to shared_task
        @shared_task(*args, **kwargs)
        @wraps(func)
        def task(environment_name, *task_args, **task_kwargs):
            try:
                environment = Environment.objects.get(name=environment_name)
            except Environment.DoesNotExist:
                raise ValueError('No environment found with name {}'.format(environment_name))

            try:
                # Call our actual task function and catch some common errors
                func(environment, *task_args, **task_kwargs)

                if not final_task:
                    # Everything went OK, set back to queued
                    environment.activity = Activity.QUEUED
                    environment.save()

            except EnvironmentTaskException as e:
                environment.activity = Activity.IDLE
                environment.save()
                logger.exception(e)
                raise
            except Exception as e:
                environment.activity = Activity.IDLE
                environment.save()
                logger.exception(e)
                raise

        return task

    return wrapped


@environment_task(name='environments.sync_all')
def sync_all(environment):
    logger.info('Syncing all salt systems for environment: {0!r}'.format(environment))

    client = salt.client.LocalClient(settings.STACKDIO_CONFIG.salt_master_config)

    ret = client.cmd_iter('env:environments.{}'.format(environment.name),
                          'saltutil.sync_all',
                          expr_form='grain')

    result = {}
    for res in ret:
        for host, data in res.items():
            result[host] = data

    for host, data in result.items():
        if 'retcode' not in data:
            logger.warning('Host {0} missing a retcode... assuming failure'.format(host))

        if data.get('retcode', 1) != 0:
            err_msg = six.text_type(data['ret'])
            raise EnvironmentTaskException('Error syncing salt data: {0!r}'.format(err_msg))


@environment_task(name='environments.highstate')
def highstate(environment, max_attempts=3):
    """
    Executes the state.highstate function on the environment using the default
    stackdio top file. That top tile will only target the 'base'
    environment and core states for the environment. These core states are
    purposely separate from others to provision hosts with things that
    stackdio needs.
    """
    environment.activity = Activity.PROVISIONING
    environment.save()

    logger.info('Running core provisioning for environment: {0!r}'.format(environment))

    # Set up logging for this task
    root_dir = environment.get_root_directory()
    log_dir = environment.get_log_directory()

    # Build up our highstate function
    @auto_retry('highstate', max_attempts, EnvironmentTaskException)
    def do_highstate(attempt=None):

        logger.info('Task {0} try #{1} for environment {2!r}'.format(
            highstate.name,
            attempt,
            environment))

        # Use our fancy context manager that handles logging for us
        with StackdioLocalClient(run_type='provisioning',
                                 root_dir=root_dir,
                                 log_dir=log_dir) as client:

            results = client.run('env:environments.{}'.format(environment.name),
                                 'state.highstate',
                                 expr_form='grain')

            if results['failed']:
                raise EnvironmentTaskException(
                    'Core provisioning errors on hosts: '
                    '{0}. Please see the provisioning errors API '
                    'or the log file for more details.'.format(', '.join(results['failed_hosts']))
                )

    # Call our highstate.  Will raise the appropriate exception if it fails.
    do_highstate()


@environment_task(name='environments.propagate_ssh')
def propagate_ssh(environment, max_attempts=3):
    """
    Similar to environments.highstate, except we only run `core.stackdio_users`
    instead of `core.*`.  This is useful so that ssh keys can be added to
    hosts without having to completely re run provisioning.
    """
    environment.activity = Activity.PROVISIONING
    environment.save()

    logger.info('Propagating ssh keys on environment: {0!r}'.format(environment))

    # Set up logging for this task
    root_dir = environment.get_root_directory()
    log_dir = environment.get_log_directory()

    @auto_retry('propagate_ssh', max_attempts, EnvironmentTaskException)
    def do_propagate_ssh(attempt=None):
        logger.info('Task {0} try #{1} for environment {2!r}'.format(
            propagate_ssh.name,
            attempt,
            environment))

        # Use our fancy context manager that handles logging for us
        with StackdioLocalClient(run_type='propagate-ssh',
                                 root_dir=root_dir,
                                 log_dir=log_dir) as client:

            results = client.run('env:environments.{}'.format(environment.name),
                                 'state.sls',
                                 arg=['core.stackdio_users'],
                                 expr_form='grain')

            if results['failed']:
                raise EnvironmentTaskException(
                    'SSH key propagation errors on hosts: '
                    '{0}. Please see the provisioning errors API '
                    'or the log file for more details.'.format(', '.join(results['failed_hosts']))
                )

    # Call our function
    do_propagate_ssh()


@environment_task(name='environments.orchestrate')
def orchestrate(environment, max_attempts=3):
    """
    Executes the runners.state.orchestrate function with the
    orchestrate sls specified on the environment.
    """
    environment.activity = Activity.ORCHESTRATING
    environment.save()

    logger.info('Executing orchestration for environment: {0!r}'.format(environment))

    # Set up logging for this task
    root_dir = environment.get_root_directory()
    log_dir = environment.get_log_directory()

    @auto_retry('orchestrate', max_attempts, EnvironmentTaskException)
    def do_orchestrate(attempt=None):
        logger.info('Task {0} try #{1} for environment {2!r}'.format(
            orchestrate.name,
            attempt,
            environment))

        with StackdioRunnerClient(run_type='orchestration',
                                  root_dir=root_dir,
                                  log_dir=log_dir) as client:

            try:
                result = client.orchestrate(arg=[
                    environment.orchestrate_sls_path,
                    'environments.{0}'.format(environment.name),
                ])
            except StackdioSaltClientException as e:
                raise EnvironmentTaskException('Orchestration failed: {}'.format(six.text_type(e)))

            # Set the statuses
            utils.set_component_statuses(environment, result)

            if result['failed']:
                err_msg = 'Orchestration errors on components: ' \
                          '{0}. Please see the orchestration errors ' \
                          'API or the orchestration log file for more ' \
                          'details.'.format(', '.join(result['failed_sls']))
                raise EnvironmentTaskException(err_msg)

    # Call our function
    do_orchestrate()


@environment_task(name='environments.single_sls')
def single_sls(environment, component, host_target, max_attempts=3):
    environment.activity = Activity.ORCHESTRATING
    environment.save()

    logger.info('Executing single sls {0} for environment: {1!r}'.format(component, environment))

    # Set up logging for this task
    root_dir = environment.get_root_directory()
    log_dir = environment.get_log_directory()

    if host_target:
        target = '{0} and G@env:environments.{1}'.format(host_target, environment.name)
        expr_form = 'compound'
    else:
        target = 'env:environments.{0}'.format(environment.name)
        expr_form = 'grain'

    @auto_retry('single_sls', max_attempts, EnvironmentTaskException)
    def do_single_sls(attempt=None):
        logger.info('Task {0} try #{1} for environment {2!r}'.format(
            single_sls.name,
            attempt,
            environment,
        ))

        with StackdioLocalClient(run_type='single-sls',
                                 root_dir=root_dir,
                                 log_dir=log_dir) as client:

            results = client.run(
                target,
                'state.sls',
                arg=[
                    component,
                    'environments.{0}'.format(environment.name),
                ],
                expr_form=expr_form,
            )

            if results['failed']:
                raise EnvironmentTaskException(
                    'Single SLS {} errors on hosts: '
                    '{}. Please see the provisioning errors API '
                    'or the log file for more details.'.format(
                        component,
                        ', '.join(results['failed_hosts']),
                    )
                )

            if results['succeeded_hosts']:
                environment.set_component_status(component, ComponentStatus.SUCCEEDED,
                                                 results['succeeded_hosts'])

            if results['failed_hosts']:
                environment.set_component_status(component, ComponentStatus.FAILED,
                                                 results['failed_hosts'])

    # Call our function
    do_single_sls()


@environment_task(name='environments.finish_environment', final_task=True)
def finish_environment(environment):
    logger.info('Finishing environment: {0!r}'.format(environment))

    # Update activity
    environment.activity = Activity.IDLE
    environment.save()
