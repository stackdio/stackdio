#!/bin/bash

set -e

# Create the stackdio user
useradd -m -s/bin/bash -U stackdio

# Create our directories
mkdir /etc/stackdio
mkdir -p /var/lib/stackdio
mkdir -p /var/log/stackdio
chown -R stackdio:stackdio /var/lib/stackdio
chown -R stackdio:stackdio /var/log/stackdio

# Make sure everything has the right permissions
mv /tmp/stackdio-init /etc/init.d/stackdio
mv /tmp/stackdio-command /usr/bin/stackdio
chown root:root /etc/init.d/stackdio
chmod 755 /etc/init.d/stackdio
chown root:root /usr/bin/stackdio
chmod 755 /usr/bin/stackdio

# Create the database
mysql -u root <<EOF
create database stackdio;
grant all on stackdio.* to stackdio@'localhost' identified by 'password';
EOF

# Create the virtualenv
virtualenv /usr/share/stackdio
. /usr/share/stackdio/bin/activate

pip install -U pip

# Install the tarball we uploaded
pip install /tmp/stackdio_server-${STACKDIO_VERSION}-py2-none-any.whl[production,mysql]

# Configure Nginx
mv /tmp/stackdio-nginx /etc/nginx/sites-available/stackdio
chown root:root /etc/nginx/sites-available/stackdio
ln -s /etc/nginx/sites-available/stackdio /etc/nginx/sites-enabled

# remove the default configuration symlink for nginx
rm /etc/nginx/sites-enabled/default

# Configure supervisor
mv /tmp/stackdio-supervisord /etc/stackdio/supervisord.conf
chown root:root /etc/stackdio/supervisord.conf

# Make sure stackdio starts at boot
update-rc.d stackdio defaults
