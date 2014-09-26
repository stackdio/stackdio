'''
Extension of the built-in file module to support an arbitrary `exists` method 
for knowing if a file, directory, device, symlink, etc exists or not. The
existing methods `file_exists` and `directory_exists` only look at those 
types, so there's not a convenient way of checking if /dev/xvdj exists for 
example.
'''

import salt.utils
import os.path

__virtualname__ = 'file'

def __virtual__():
    '''
    Only work on POSIX-like systems
    '''
    # win_file takes care of windows
    if salt.utils.is_windows():
        return False
    return 'file'


def exists(path):
    '''
    Tests to see if a path exists.  Returns True/False.

    CLI Example::

        salt '*' file.exists /dev/xvdj

    '''
    return os.path.exists(path)
