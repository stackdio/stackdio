'''
Loads a stack-specific pillar file. stack_pillar_file must be set in the grains
or this module will not be available to pillar.
'''

import logging
import yaml

# Set up logging
logger = logging.getLogger(__name__)


def __virtual__():
    '''
    '''

    # Only load the module if stack_pillar_file has been set.
    return 'stackdio' if 'stack_pillar_file' in __grains__ else False  # NOQA


def ext_pillar(pillar, *args, **kwargs):
    '''
    Basically, we need to providee additional pillar data to our states
    but only the pillar data defined for a stack. The user should have
    the ability to do this from the UI and the pillar file used will
    be located in the grains.
    '''

    # load the stack_pillar_file, rendered as yaml, and return it
    d = {}
    try:
        with open(__grains__['stack_pillar_file'], 'r') as f:  # NOQA
            d = yaml.safe_load(f)
            d['stack_pillar_available'] = True
    except Exception, e:
        logger.exception(e)
        logger.critical('Unable to load/render stack_pillar_file. Is the YAML '
                        'properly formatted?')
    return d
