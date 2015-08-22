#!/bin/bash

set -e

stackdio init <<EOF
stackdio
/var/lib/stackdio


mysql://stackdio:password@localhost:3306/stackdio
true
yes
EOF

stackdio manage.py migrate

# Create our superuser
stackdio manage.py loaddata /tmp/stackdio-data.json

stackdio manage.py collectstatic --noinput
