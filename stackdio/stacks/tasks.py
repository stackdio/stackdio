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

        stack.status = 'launching'
        stack.save()

        # TODO: It would be nice if we could control the salt-cloud log
        # file at runtime

        # Get paths
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        map_file = stack.map_file.path
        log_file = stack.map_file.path + '.{}.log'.format(now)

        # Launch stack
        result = envoy.run(' '.join([
            'salt-cloud',
            '-y',                    # assume yes
            '-lquiet',               # no logging on console
            '--log-file {0}',        # where to log
            '--log-file-level all',  # full logging
            '--out json',            # return JSON formatted results
            '--out-indent -1',       # don't format them; this is because of
                                     # a bug in salt-cloud
            '-m {1}',                # the map file to use for launching
        ]).format(log_file, map_file))

        if result.status_code > 0:
            stack.status = Stack.ERROR
            stack.status_detail = result.std_err \
                if len(result.std_err) else result.std_out
            stack.save()
            return

        # TODO: Run highstate machines with this stack id
        # e.g, `salt 'stack_id:{0}'.format(stack_id) state.highstate`
        #envoy.run('salt \'{}\' state.highstate'.format('*'))

        stack.status = 'provisioning'
        stack.save()
        time.sleep(5)

        # highstate, targeting only this stack
        # result = envoy.run(' '.join([
        #     'salt',
        #     'G:{}'                  # targeting a specific grain attribute
        #     'state.highstate',      # highstate!
        # ]).format(stack_id))

        stack.status = 'finished'
        stack.save()

    except Stack.DoesNotExist:
        logger.error('Attempted to launch an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while launching a Stack')
        stack.status = 'error'
        stack.status_detail = str(e)
        stack.save()
