#!/bin/bash

set -e

# Need to stop ntp before syncing
service ntp stop || echo 'ntp already stopped'
ntpdate 0.pool.ntp.org 1.pool.ntp.org 2.pool.ntp.org 3.pool.ntp.org
service ntp start

# Create the stackdio user
useradd -m -s/bin/bash -U stackdio

# Create our directories
mkdir /etc/stackdio
mkdir -p /var/lib/stackdio
mkdir -p /var/log/stackdio
mkdir -p /var/cache/salt
chown -R stackdio:stackdio /var/lib/stackdio
chown -R stackdio:stackdio /var/log/stackdio
chown -R stackdio:stackdio /var/cache/salt

# Make sure everything has the right permissions
mv /tmp/stackdio-init /etc/init.d/stackdio
mv /tmp/stackdio-command /usr/bin/stackdio
chown root:root /etc/init.d/stackdio
chmod 755 /etc/init.d/stackdio
chown root:root /usr/bin/stackdio
chmod 755 /usr/bin/stackdio

# Create the database
sudo -u postgres psql postgres <<EOF
CREATE USER stackdio WITH UNENCRYPTED PASSWORD 'password';
CREATE DATABASE stackdio;
ALTER DATABASE stackdio OWNER to stackdio;
EOF

# Create the virtualenv
virtualenv /usr/share/stackdio
. /usr/share/stackdio/bin/activate

pip install -U pip wheel setuptools

# Install stackdio-server from pypi
pip install "stackdio-server[postgresql,production]==${STACKDIO_VERSION}"

# Configure Nginx
mv /tmp/stackdio-nginx /etc/nginx/sites-available/stackdio
chown root:root /etc/nginx/sites-available/stackdio
ln -s /etc/nginx/sites-available/stackdio /etc/nginx/sites-enabled

# remove the default configuration symlink for nginx
rm /etc/nginx/sites-enabled/default

# Configure supervisor
mv /tmp/stackdio-supervisord /etc/stackdio/supervisord.conf
chown root:root /etc/stackdio/supervisord.conf

mv /tmp/stackdio.yaml /etc/stackdio/stackdio.yaml
chown root:root /etc/stackdio/stackdio.yaml

# Make sure stackdio starts at boot
update-rc.d stackdio defaults
