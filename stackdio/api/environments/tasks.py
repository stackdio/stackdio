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

import logging
from functools import wraps

import six
from celery import shared_task

from stackdio.api.environments.exceptions import EnvironmentTaskException
from stackdio.api.environments.models import Environment
from stackdio.api.environments import utils
from stackdio.core.constants import Activity
from stackdio.core.utils import auto_retry
from stackdio.salt.utils.client import StackdioRunnerClient, StackdioSaltClientException

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
                environment.log_history(six.text_type(e), Activity.IDLE)
                logger.exception(e)
                raise
            except Exception as e:
                err_msg = 'Unhandled exception: {0}'.format(e)
                environment.log_history(err_msg, Activity.IDLE)
                logger.exception(e)
                raise

        return task

    return wrapped


@environment_task(name='environments.orchestrate')
def orchestrate(environment, max_attempts=3):
    """
    Executes the runners.state.orchestrate function with the
    orchestrate sls specified on the environment.
    """
    environment.set_activity(Activity.ORCHESTRATING)

    logger.info('Executing orchestration for environment: {0!r}'.format(environment))

    # Set up logging for this task
    root_dir = environment.get_root_directory()
    log_dir = environment.get_log_directory()

    @auto_retry('orchestrate', max_attempts)
    def do_orchestrate(attempt=None):
        logger.info('Task {0} try #{1} for environment {2!r}'.format(
            orchestrate.name,
            attempt,
            environment))

        # Update status
        environment.log_history(
            'Executing orchestration try {0} of {1}. This '
            'may take a while.'.format(
                attempt,
                max_attempts,
            )
        )

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

    environment.log_history('Finished executing orchestration all hosts.')
