import time

import celery
from celery.utils.log import get_task_logger
from saltcloud.cli import SaltCloud

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

        client = SaltCloud()
        args = [
            '-y',                   # Assume yes to everything
            '-l',                   # Log level
            'error',
            '-P',                   # Parallelize it
            '-m',                   # Specify the map file  to use
            stack.map_file.path
        ]
        x = client.run(args)

        # TODO: Run highstate machines with this stack id
        # e.g, `salt 'stack_id:{0}'.format(stack_id) state.highstate`
        stack.status = 'provisioning'
        stack.save()
        time.sleep(5)

        stack.status = 'finished'
        stack.save()

    except Stack.DoesNotExist:
        logger.error('Attempted to launch an unknown Stack with id {}' \
            .format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while launching a Stack')
        stack.status = 'error'
        stack.status_detail = str(e)
        stack.save()
