#!/bin/bash

set -e

stackdio manage.py migrate

# Create our superuser
stackdio manage.py loaddata /tmp/stackdio-data.json

stackdio manage.py collectstatic --noinput
