'''
Extension of the built-in mount module to add a few methods we need for
when operating with ebs volumes.
'''

import salt.utils
import os.path

__virtualname__ = 'mount'

def __virtual__():
    '''
    Only work on POSIX-like systems
    '''
    # win_file takes care of windows
    if salt.utils.is_windows():
        return False
    return 'mount'


def find_ebs_device(device):
    '''
    Tests to see if `device` exists or the xvd derivative. Returns
    None if no device could be found.

    CLI Example::

        salt '*' mount.exists /dev/sdj
        salt '*' mount.exists /dev/xvdj

    '''
    if os.path.exists(device):
        return device

    if device.startswith('/dev/sd'):
        new_device = '/dev/xvd' + device[device.rfind('/')+3:]
        if os.path.exists(new_device):
            return new_device

    return None

