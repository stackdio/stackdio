import celery
import time

@celery.task(name='core.sleep')
def sleep(seconds=10):
    time.sleep(seconds)
    return True
