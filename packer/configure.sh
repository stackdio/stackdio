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

stackdio manage.py createsuperuser <<EOF
admin
stackdio@stackd.io
stackdio
stackdio
EOF

stackdio manage.py collectstatic --noinput
