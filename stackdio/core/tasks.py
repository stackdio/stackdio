from celery import task
from time import sleep

@task
def create_user(**kwargs):
    sleep(4)
    return {
        'name': 'abe',
    }

