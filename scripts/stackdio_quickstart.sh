#!/bin/bash

##########
#
# This script follows very closely with the Quick Start code located at
# https://github.com/digitalreasoning/stackdio.git. The intent is to
# plop this on a server and run it to quickly get a functional stackd.io
# environment.
#
# Feel free to make tweaks to suit your needs.
#
##########

# Create stackdio user if necessary
if ! id -u stackdio &> /dev/null; then
    sudo useradd -m -s/bin/bash -U stackdio
    sudo echo 'stackdio ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/stackdio > /dev/null
    sudo cp $0 ~stackdio/stackdio_quickstart.sh
    sudo chown stackdio:stackdio ~stackdio/stackdio_quickstart.sh

    echo "stackdio user created..."
    echo "Please switch to the stackdio user and run ~/stackdio_quickstart.sh"
    exit 0
fi

# Prevent script from running as anyone but the stackdio user
if [ `id -u -n` != "stackdio" ]; then
    echo "Please run this script as the stackdio user"
    exit 1
fi

# detect OS (centos or ubuntu only)
OS=
if `which lsb_release &> /dev/null`; then

    if lsb_release -a 2>/dev/null | grep -i ubuntu &>/dev/null; then
        OS=ubuntu
    elif lsb_release -a 2>/dev/null | grep -i centos &>/dev/null; then
        OS=centos
    fi

elif [ -f "/etc/os-release" ] && grep --quiet "ubuntu" "/etc/os-release"; then
    OS=ubuntu
elif [ -f "/etc/redhat-release" ] && grep --quiet -i "centos" "/etc/redhat-release"; then
    OS=centos
fi

# bail out if we couldn't figure out the OS
if [ -z "$OS" ]; then
    echo "Could not determine OS. Aborting."
    exit 1
fi

###
# CORE STEPS
###

# XXX: Remove this after making stackdio public

# Private key for github access...use your own please :)
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat > ~/.ssh/id_rsa <<EOF
-----BEGIN RSA PRIVATE KEY-----
INSERT
YOUR
OWN
KEY
HERE
-----END RSA PRIVATE KEY-----
EOF

chmod 600 ~/.ssh/id_rsa
# XXX: End

###
# CENTOS PREP
###
if [ $OS == "centos" ]; then

    sudo yum install -y mysql-server
    sudo service mysqld start

    echo "create database stackdio; \
    grant all on stackdio.* to stackdio@'localhost' identified by 'password';" | \
    mysql -h localhost -u root

    sudo yum install -y python-virtualenvwrapper
    echo "source /usr/bin/virtualenvwrapper.sh" >> ~/.bash_profile
    . ~/.bash_profile

    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y git mysql-devel swig python-devel rabbitmq-server nginx

fi

###
# UBUNTU PREP
###
if [ $OS == "ubuntu" ]; then

    sudo apt-get install -y mysql-server mysql-client

    echo "create database stackdio; \
    grant all on stackdio.* to stackdio@'localhost' identified by 'password';" | \
    mysql -hlocalhost -uroot -ppassword

    sudo apt-get install -y virtualenvwrapper
    source /etc/bash_completion.d/virtualenvwrapper

    sudo apt-get install -y python-dev libssl-dev libncurses5-dev swig libmysqlclient-dev rabbitmq-server git nginx

fi

###
# CORE STEPS CONTINUED
###

# Create the virtualenv and make sure to install everything into it
mkvirtualenv stackdio
workon stackdio

cd /tmp

# Prevent host checking when cloning from github
cat >> ~/.ssh/config << EOF
Host github.com
    StrictHostKeyChecking no

EOF
chmod 600 ~/.ssh/config

# Install directly from GitHub
pip install git+ssh://git@github.com/digitalreasoning/stackdio.git

# Run through stackdio init to create ~/.stackdio/confg
stackdio init

# Set up the database
stackdio manage.py syncdb --noinput
stackdio manage.py migrate

if [ $OS == "centos" ]; then
    # fix home directory permissions
    chmod +x ~/

    # move existing centos default configuration if needed
    test -f "/etc/nginx/conf.d/default.conf" && sudo mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak
    stackdio config nginx | sudo tee /etc/nginx/conf.d/stackdio.conf > /dev/null
else
    # remove existing ubuntu default configuration symlink
    test -f "/etc/nginx/sites-enabled/default" && sudo rm -rf /etc/nginx/sites-enabled/default

    # generate nginx config
    stackdio config nginx | sudo tee /etc/nginx/sites-available/stackdio > /dev/null

    # symlink
    test -f "/etc/nginx/sites-enabled/stackdio" && sudo rm -rf /etc/nginx/sites-enabled/stackdio
    sudo ln -s /etc/nginx/sites-available/stackdio /etc/nginx/sites-enabled
fi

# Generate static content
stackdio manage.py collectstatic --noinput

# Restart nginx
sudo service nginx restart

# Start rabbitmq-server
sudo service rabbitmq-server start

# Generate supervisord config and start services
stackdio config supervisord > ~/.stackdio/supervisord.conf
supervisord -c ~/.stackdio/supervisord.conf
supervisorctl -c ~/.stackdio/supervisord.conf start all

