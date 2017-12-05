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

from __future__ import absolute_import, print_function, unicode_literals

import io
import logging
import os
import re
from datetime import datetime

import salt.client
import salt.config
import salt.runner
import six
import yaml
from django.conf import settings

from stackdio.salt.utils.logging import setup_logfile_logger

logger = logging.getLogger(__name__)
root_logger = logging.getLogger()


COLOR_REGEX = re.compile(r'\[0;[\d]+m')

ERROR_REQUISITE = 'One or more requisite failed'


class StackdioSaltClientException(Exception):
    pass


def is_state_error(state_meta):
    """
    Determines if the state resulted in an error.
    """
    return not state_meta['result']


def state_to_dict(state_string):
    """
    Takes the state string and transforms it into a dict of key/value
    pairs that are a bit easier to handle.

    Before: group_|-stackdio_group_|-abe_|-present

    After: {
        'module': 'group',
        'function': 'present',
        'name': 'abe',
        'declaration_id': 'stackdio_group'
    }
    """
    state_labels = settings.STATE_EXECUTION_FIELDS
    state_fields = state_string.split(settings.STATE_EXECUTION_DELIMITER)
    return dict(zip(state_labels, state_fields))


def is_requisite_error(state_meta):
    """
    Is the state error because of a requisite state failure?
    """
    return ERROR_REQUISITE in state_meta['comment']


def is_recoverable(err):
    """
    Checks the provided error against a blacklist of errors
    determined to be unrecoverable. This should be used to
    prevent retrying of provisioning or orchestration because
    the error will continue to occur.
    """
    # TODO: determine the blacklist of errors that
    # will trigger a return of False here
    return True


def state_error(state_str, state_meta):
    """
    Takes the given state result string and the metadata
    of the state execution result and returns a consistent
    dict for the error along with whether or not the error
    is recoverable.
    """
    state = state_to_dict(state_str)
    func = '{module}.{func}'.format(**state)
    decl_id = state['declaration_id']
    err = {
        'error': state_meta['comment'],
        'function': func,
        'declaration_id': decl_id,
    }
    if 'stderr' in state_meta['changes']:
        err['stderr'] = state_meta['changes']['stderr']
    if 'stdout' in state_meta['changes']:
        err['stdout'] = state_meta['changes']['stdout']
    return err, is_recoverable(err)


def process_sls_result(sls_result, err_file):
    if 'out' in sls_result and sls_result['out'] != 'highstate':
        logger.debug('This isn\'t highstate data... it may not process correctly.')

        raise StackdioSaltClientException('Missing highstate data from the orchestrate runner.')

    ret = {
        'failed': False,
        'succeeded_hosts': set(),
        'failed_hosts': set(),
    }

    if 'ret' not in sls_result:
        ret['failed'] = True
        return ret

    # Loop over the host items
    for host, state_results in sls_result['ret'].items():
        sorted_result = sorted(state_results.values(), key=lambda x: x['__run_num__'])
        for stage_result in sorted_result:

            if stage_result.get('result', False):
                # Result is true, we succeeded
                ret['succeeded_hosts'].add(host)
                continue

            # We have failed - add ourselves to the failure list
            ret['failed'] = True
            ret['failed_hosts'].add(host)

            # Check to see if it's a requisite error - if so, we don't want to clutter the
            # logs, so we'll continue on.
            if is_requisite_error(stage_result):
                continue

            # Write to the error log
            with io.open(err_file, 'at') as f:
                yaml.safe_dump(stage_result, f)

    return ret


def process_times(sls_result):
    if 'ret' not in sls_result:
        return

    max_time_map = {}

    for state_results in sls_result['ret'].values():
        for stage_label, stage_result in state_results.items():

            # Pull out the duration
            if 'duration' in stage_result:
                current = max_time_map.get(stage_label, 0)
                duration = stage_result['duration']
                try:
                    if isinstance(duration, six.string_types):
                        new_time = float(duration.split()[0])
                    else:
                        new_time = float(duration)
                except ValueError:
                    # Make sure we never fail
                    new_time = 0

                # Only set the duration if it's higher than what we already have
                # This should be all we care about - since everything is running in parallel,
                # the bottleneck is the max time
                max_time_map[stage_label] = max(current, new_time)

    time_map = {}

    # aggregate into modules
    for stage_label, max_time in max_time_map.items():
        info_dict = state_to_dict(stage_label)

        current = time_map.get(info_dict['module'], 0)

        # Now we want the sum since these are NOT running in parallel.
        time_map[info_dict['module']] = current + max_time

    for smodule, time in sorted(time_map.items()):
        logger.info('Module {0} took {1} total seconds to run'.format(smodule, time / 1000))


def process_orchestrate_result(result, err_file):
    ret = {
        'failed': False,
        'succeeded_sls': {},
        'failed_sls': {},
        'cancelled_sls': {},
    }

    if 'data' not in result:
        with io.open(err_file, 'at') as f:
            f.write('Orchestration result is missing information:\n\n')
            f.write(six.text_type(result))
        ret['failed'] = True
        return ret

    # The actual info we want is nested in the 'data' key
    result = result['data']

    opts = salt.config.client_config(settings.STACKDIO_CONFIG.salt_master_config)

    if not isinstance(result, dict):
        with io.open(err_file, 'at') as f:
            f.write('Orchestration failed.  See below.\n\n')
            f.write(six.text_type(result))
        ret['failed'] = True
        return ret

    if opts['id'] not in result:
        with io.open(err_file, 'at') as f:
            f.write('Orchestration result is missing information:\n\n')
            f.write(six.text_type(result))
        ret['failed'] = True
        return ret

    result = result[opts['id']]

    if not isinstance(result, dict):
        with io.open(err_file, 'at') as f:
            f.write(six.text_type(result))

        raise StackdioSaltClientException(result)

    for sls, sls_result in sorted(result.items(), key=lambda x: x[1]['__run_num__']):
        sls_dict = state_to_dict(sls)

        logger.info('Processing stage {0}'.format(sls_dict['name']))

        if 'changes' in sls_result:
            process_times(sls_result['changes'])

        logger.info('')

        if sls_result.get('result', False):
            # This whole sls is good!  Add that to the ret dict and move on.
            sls_ret_dict = {
                'failed': False,
                'failed_hosts': set(),
                'succeeded_hosts': set(),
            }

            if 'changes' in sls_result:
                sls_ret_dict['succeeded_hosts'] = set(sls_result['changes'].get('ret', {}).keys())

            # Write a message to the error log
            with io.open(err_file, 'at') as f:
                if sls_ret_dict['succeeded_hosts']:
                    f.write(
                        'Stage {} succeeded and returned {} host info object{}\n\n'.format(
                            sls_dict['name'],
                            len(sls_ret_dict['succeeded_hosts']),
                            '' if len(sls_ret_dict['succeeded_hosts']) == 1 else 's',
                        )
                    )
                else:
                    f.write('Stage {} succeeded, but appears to have no changes.\n\n'.format(
                        sls_dict['name'],
                    ))

            # Add to the success map
            ret['succeeded_sls'][sls_dict['name']] = sls_ret_dict
        else:
            # We failed - print a message to the log.
            with io.open(err_file, 'at') as f:
                if 'changes' in sls_result and 'ret' in sls_result['changes']:
                    f.write(
                        'Stage {} failed and returned {} host info object{}\n\n'.format(
                            sls_dict['name'],
                            len(sls_result['changes']['ret']),
                            '' if len(sls_result['changes']['ret']) == 1 else 's',
                        )
                    )
                else:
                    f.write(
                        'Stage {} failed, but appears to have no changes. See below.\n'.format(
                            sls_dict['name'],
                        )
                    )

                # Print the failure comment
                if 'comment' in sls_result:
                    comment = sls_result['comment']
                    if isinstance(comment, six.string_types):
                        f.write('{}\n\n'.format(COLOR_REGEX.sub('', comment)))
                    else:
                        f.write('{}\n\n'.format(yaml.safe_dump(comment)))

            if 'changes' in sls_result:
                # Process the info to see which hosts failed (will then print more info)
                sls_ret_dict = process_sls_result(sls_result['changes'], err_file)
            else:
                # Just set it to empty since we have no changes to go off of
                sls_ret_dict = {
                    'failed': True,
                    'failed_hosts': set(),
                    'succeeded_hosts': set(),
                }

            # Add to the failure sls list
            ret['failed'] = True
            if ERROR_REQUISITE in sls_result['comment']:
                # Requisite error means we were cancelled
                ret['cancelled_sls'][sls_dict['name']] = sls_ret_dict
            else:
                # No requisite error, we actually failed
                ret['failed_sls'][sls_dict['name']] = sls_ret_dict

    return ret


class LoggingContextManager(object):

    def __init__(self, run_type, root_dir, log_dir):
        self.run_type = run_type
        self.root_dir = root_dir
        self.log_dir = log_dir

        self.log_file = None
        self.err_file = None

        self._file_log_handler = None
        self._old_handlers = []

    @staticmethod
    def _symlink(source, target):
        """
        Symlink the given source to the given target
        """
        if os.path.islink(target):
            os.remove(target)
        # Do a relative symlink instead of absolute
        os.symlink(os.path.relpath(source, os.path.dirname(target)), target)

    def _set_up_logging(self):
        now = datetime.now().strftime('%Y%m%d-%H%M%S')
        self.log_file = os.path.join(self.log_dir, '{}.{}.log'.format(now, self.run_type))
        self.err_file = os.path.join(self.log_dir, '{}.{}.err'.format(now, self.run_type))
        log_symlink = os.path.join(self.root_dir, '{}.log.latest'.format(self.run_type))
        err_symlink = os.path.join(self.root_dir, '{}.err.latest'.format(self.run_type))

        # "touch" the log file and symlink it to the latest
        for l in (self.log_file, self.err_file):
            with io.open(l, 'w') as _:
                pass
        self._symlink(self.log_file, log_symlink)
        self._symlink(self.err_file, err_symlink)

        self._file_log_handler = setup_logfile_logger(self.log_file)

        # Remove the other handlers, but save them so we can put them back later
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                self._old_handlers.append(handler)
                root_logger.removeHandler(handler)

    def _tear_down_logging(self):
        # First remove our new log handler if it exists
        if self._file_log_handler:
            root_logger.removeHandler(self._file_log_handler)

        # Then re-add the old handlers we removed earlier
        for handler in self._old_handlers:
            root_logger.addHandler(handler)

        # Reset our variables
        self._file_log_handler = None
        self._old_handlers = []

    # Make it a context manager
    def __enter__(self):
        self._set_up_logging()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._tear_down_logging()


class StackdioLocalClient(LoggingContextManager):

    def __init__(self, *args, **kwargs):
        super(StackdioLocalClient, self).__init__(*args, **kwargs)
        self.salt_client = salt.client.LocalClient(settings.STACKDIO_CONFIG.salt_master_config)

    def run(self, target, function, **kwargs):
        result = self.salt_client.cmd_iter(target, function, **kwargs)

        ret = {
            'failed': False,
            'failed_hosts': set(),
            'succeeded_hosts': set(),
            'num_hosts': 0,
        }

        for i in result:
            for host, result in i.items():
                ret['num_hosts'] += 1
                host_errors = self.process_result(host, result)
                if host_errors:
                    # We failed.
                    ret['failed'] = True
                    ret['failed_hosts'].add(host)
                    with io.open(self.err_file, 'at') as f:
                        f.write('Errors on host {}:\n'.format(host))
                        yaml.safe_dump(host_errors, f)
                        f.write('\n')
                else:
                    # We succeeded!
                    ret['succeeded_hosts'].add(host)

        return ret

    @staticmethod
    def process_result(host, result):
        """
        Process the host result.  Should return a list of errors, an empty list
        signifying no errors were found.
        :param host: the name of the host
        :param result: the host dictionary
        :return: a list of errors
        """
        logger.debug('result for {}: {}'.format(host, result))
        states = result['ret']

        errors = []

        # If we don't have a dict-like object, we know we have an error, just return the states
        if not isinstance(states, dict):
            return states

        for state_str, state_meta in states.items():
            if not is_state_error(state_meta):
                # Just go on to the next one, no error found
                continue

            # Now we know there is an error
            if not is_requisite_error(state_meta):
                # But we only care about it if it's not a requisite error
                err, _ = state_error(state_str, state_meta)
                errors.append(err)

        return errors


class StackdioRunnerClient(LoggingContextManager):

    def __init__(self, *args, **kwargs):
        super(StackdioRunnerClient, self).__init__(*args, **kwargs)
        opts = salt.config.client_config(settings.STACKDIO_CONFIG.salt_master_config)
        self.salt_runner = salt.runner.RunnerClient(opts)

    def orchestrate(self, **kwargs):
        result = self.salt_runner.cmd('state.orchestrate', **kwargs)
        return process_orchestrate_result(result, self.err_file)
