#!/bin/bash

# Create the stackdio user
useradd -m -s/bin/bash -U stackdio

# Create our directories
mkdir /etc/stackdio
mkdir /var/lib/stackdio
chown stackdio:stackdio /var/lib/stackdio
chown root:root /etc/init.d/stackdio

# Create the database
echo "create database stackdio; grant all on stackdio.* to stackdio@'localhost' identified by 'password';" | \
mysql -hlocalhost -uroot -ppassword

# Create the virtualenv
virtualenv /usr/share/stackdio
source /usr/share/stackdio/bin/activate

# Install the tarball we uploaded
pip install /tmp/stackdio-server.tar.gz

stackdio init < cat <<EOF
stackdio
/var/lib/stackdio


mysql://stackdio:password@localhost:3306/stackdio
true
EOF

stackdio manage.py migrate

# Somehow?
#  stackdio manage.py createsuperuser

# Nginx
stackdio config nginx | tee /etc/nginx/sites-available/stackdio > /dev/null
ln -s /etc/nginx/sites-available/stackdio /etc/nginx/sites-enabled

# remove the default configuration symlink
rm /etc/nginx/sites-enabled/default

stackdio manage.py collectstatic --noinput

service nginx restart

service rabbitmq-server start

stackdio config supervisord > /etc/stackdio/supervisord.conf

