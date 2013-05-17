#!/usr/bin/env python
import os
import sys

##
# Defaulting to local settings module for a single dev machine.
# Override this to be a new module in stackdio/settings or you
# may pass in this as an environment variable.
##
DEFAULT_SETTINGS_MODULE = 'stackdio.settings.local'

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DEFAULT_SETTINGS_MODULE)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
