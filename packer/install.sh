#!/bin/bash

# Create the stackdio user
useradd -m -s/bin/bash -U stackdio

# Create our directories
mkdir /etc/stackdio
mkdir -p /var/lib/stackdio
mkdir -p /var/log/stackdio/supervisord
chown -R stackdio:stackdio /var/lib/stackdio
chown -R stackdio:stackdio /var/log/stackdio

# Make sure everything has the right permissions
chown root:root /etc/init.d/stackdio
chmod 755 /etc/init.d/stackdio
chown root:root /usr/bin/stackdio
chmod 755 /usr/bin/stackdio

# Create the database
mysql -hlocalhost -uroot -ppassword < cat <<EOF
create database stackdio
grant all on stackdio.* to stackdio@'localhost' identified by 'password'
EOF

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
#stackdio manage.py createsuperuser

# Nginx
stackdio config nginx | tee /etc/nginx/sites-available/stackdio > /dev/null
ln -s /etc/nginx/sites-available/stackdio /etc/nginx/sites-enabled

# remove the default configuration symlink
rm /etc/nginx/sites-enabled/default

stackdio manage.py collectstatic --noinput

service nginx restart

stackdio config supervisord > /etc/stackdio/supervisord.conf
