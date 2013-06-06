import celery
from celery.utils.log import get_task_logger

from .models import CloudProvider

logger = get_task_logger(__name__)


@celery.task(name='cloud.get_provider_instances')
def get_provider_instances(provider_id):
    try:
        provider = CloudProvider.objects.get(id=provider_id)
        logger.info('CloudProvider: {0!r}'.format(provider))

    except CloudProvider.DoesNotExist:
        logger.error('Unknown CloudProvider with id {}'.format(
            provider_id))
    except Exception, e:
        logger.exception('Unhandled exception retrieving instance sizes.')
