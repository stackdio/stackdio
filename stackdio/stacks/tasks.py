import time
import os.path
from datetime import datetime

import envoy
import celery
from celery.utils.log import get_task_logger

from .models import Stack

logger = get_task_logger(__name__)


def log_envoy_result(result, out_file=None, err_file=None, add_date=True):
    date_format = '%Y%m%d_%H%M%s'
    date_string = '.{}'.format(datetime.now().strftime(date_format)) if add_date else ''

    with open(out_file + date_string, 'w') as f:
        f.write(result.std_out)

    with open(err_file + date_string, 'w') as f:
        f.write(result.std_err)


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
        map_file = stack.map_file.path
        out_file = map_file + '.out'
        err_file = map_file + '.err'

        # Launch stack
        result = envoy.run('salt-cloud -y -lquiet --out json --out-indent -1 '
                           '-m {}'.format(stack.map_file.path))
        log_envoy_result(result, out_file, err_file)

        if result.status_code > 0:
            stack.status = Stack.ERROR
            stack.status_detail = result.std_err
            stack.save()
            return

        # TODO: Run highstate machines with this stack id
        # e.g, `salt 'stack_id:{0}'.format(stack_id) state.highstate`
        #envoy.run('salt \'{}\' state.highstate'.format('*'))

        stack.status = 'provisioning'
        stack.save()
        time.sleep(5)

        stack.status = 'finished'
        stack.save()

    except Stack.DoesNotExist:
        logger.error('Attempted to launch an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while launching a Stack')
        stack.status = 'error'
        stack.status_detail = str(e)
        stack.save()
