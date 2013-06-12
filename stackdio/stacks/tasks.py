import yaml
import time
import os.path
from datetime import datetime

import envoy
import celery
from celery.utils.log import get_task_logger

from .models import Stack

logger = get_task_logger(__name__)


@celery.task(name='stacks.launch_stack')
def launch_stack(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Launching new stack: {0!r}'.format(stack))

        # Use SaltCloud to launch machines using the given stack's
        # map_file that should already be generated

        stack.set_status(Stack.LAUNCHING)

        # TODO: It would be nice if we could control the salt-cloud log
        # file at runtime

        # Get paths
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        map_file = stack.map_file.path
        log_file = stack.map_file.path + '.{}.log'.format(now)

        # Launch stack
        cmd = ' '.join([
            'salt-cloud',
            '-y',                    # assume yes
            '-P',                    # parallelize VM launching
            '-lquiet',               # no logging on console
            '--log-file {0}',        # where to log
            '--log-file-level all',  # full logging
            '--out json',            # return JSON formatted results
            '--out-indent -1',       # don't format them; this is because of
                                     # a bug in salt-cloud
            '-m {1}',                # the map file to use for launching
        ]).format(log_file, map_file)

        logger.debug('Excuting command: {0}'.format(cmd))
        result = envoy.run(cmd)

        if result.status_code > 0:
            err_msg = result.std_err if len(result.std_err) else result.std_out
            stack.set_status(Stack.ERROR, err_msg)
            return

    except Stack.DoesNotExist:
        logger.error('Attempted to launch an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while launching a Stack')
        stack.set_status(Stack.ERROR, str(e))

@celery.task(name='stacks.provision_stack')
def provision_stack(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Provisioning stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(Stack.PROVISIONING)

        # Run the appropriate top file
        cmd = ' '.join([
            'salt',
            '-C',                   # compound targeting
            'G@stack_id:{}'.format(stack_id),  # target the nodes in this stack only
            'state.top',            # run this stack's top file
            stack.top_file.name,
            '--out yaml'            # output in yaml format
        ]).format(stack_id)

        logger.debug('Excuting command: {0}'.format(cmd))
        result = envoy.run(cmd)

        logger.debug('salt state.top stdout:')
        logger.debug(result.std_out)

        logger.debug('salt state.top stderr:')
        logger.debug(result.std_err)

    except Stack.DoesNotExist:
        logger.error('Attempted to provision an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while provisioning a Stack')
        stack.set_status(Stack.ERROR, str(e))


@celery.task(name='stacks.finish_stack')
def finish_stack(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Finishing stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(Stack.FINISHED)

    except Stack.DoesNotExist:
        logger.error('Attempted to provision an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while finishing a Stack')
        stack.set_status(Stack.ERROR, str(e))


@celery.task(name='stacks.destroy_stack', ignore_result=True)
def destroy_stack(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Destroying stack: {0!r}'.format(stack))

        # Check for map file, and if it doesn't exist just remove
        # the stack and return
        if not os.path.isfile(stack.map_file.path):
            logger.warn('Map file for stack {} does not exist. '
                        'Deleting stack anyway.'.format(stack))
            stack.delete()
            return

        # Run the appropriate top file
        cmd = ' '.join([
            'salt-cloud',
            '-y',                   # assume yes
            '-P',                   # destroy in parallel
            '-m {0}',               # the map file to use for launching
            '-d',                   # destroy the stack
            '--out yaml',           # output in yaml
        ]).format(stack.map_file.path)

        logger.debug('Excuting command: {0}'.format(cmd))
        result = envoy.run(cmd)

        if result.status_code > 0:
            err_msg = result.std_err if len(result.std_err) else result.std_out
            stack.set_status(Stack.ERROR, err_msg)
            return

        stack.delete()

    except Stack.DoesNotExist:
        logger.error('Attempted to destroy an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while finishing a Stack')
        stack.set_status(Stack.ERROR, str(e))
