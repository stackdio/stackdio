#!/bin/bash -e

# 
# This script starts with a bare CentOS AMI and bootstraps everything required
# to install stackd.io.  At the conclusion of this script you should be able to
# install stackd.io with bootstrap2.sh.
#

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function log_msg {
    echo "[$(date)] $1"
}

if [ ! -e /etc/redhat-release ]; then
    log_msg "This doesn't appear to be a CentOS/RHEL system, but needs to be"
    exit 1
fi

if [ "$(whoami)" != "root" ]; then 
    log_msg "Must be root to run"
    exit 1
fi

HOSTNAME=$(curl http://169.254.169.254/latest/meta-data/public-hostname)
log_msg "#####################################################################"
log_msg " Bootstrapping stackd.io installation (part 1)"
log_msg " CentOS Version  :  $(cat /etc/redhat-release)"
log_msg " Hostname        : $HOSTNAME"
log_msg "#####################################################################"

log_msg "Installing EPEL"
curl -O http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
yum -y localinstall epel-release-6-8.noarch.rpm


log_msg "Installing some prereqs"
yum groupinstall -y "Development Tools"
yum install -y python-devel ncurses-devel swig openssl-devel mercurial \
    git readline-devel screen mysql mysql-server mysql-devel \
    rabbitmq-server nginx


log_msg "Setting up and starting MySQL"
service mysqld start
MYSQL="mysql -hlocalhost -uroot"
echo "create database stackdio;" | $MYSQL
echo "create user stackdio;" | $MYSQL
echo "grant all on stackdio.* to 'stackdio'@'localhost' identified by 'password';" | $MYSQL


log_msg "Starting rabbitmq-server"
service rabbitmq-server start


# @todo this is temporary, should really just open up the desired ports
log_msg "Disabling iptables"
service iptables stop


log_msg "Setting up the stackdio user"
useradd -m -s/bin/bash -U stackdio
# this is not as "safe" as using visudo but is better than nothing
if [ -e /etc/sudoers.tmp ]; then
    log_msg "Unable to safely edit sudoers file, exiting"
    exit 1
fi
echo "stackdio ALL=(ALL)      NOPASSWD:ALL" >> /etc/sudoers


log_msg "Staging/configuring process management"
cp ${script_dir}/supervisord.conf /etc/
for ff in $(ls /etc/nginx/conf.d/*.conf); do
    mv $ff ${ff}.bak
done
cp ${script_dir}/stackdio_nginx.conf /etc/nginx/conf.d
sed -i "s/STACKDIO_HOSTNAME/$HOSTNAME/g" /etc/nginx/conf.d/stackdio_nginx.conf

service nginx start

log_msg "#####################################################################"
log_msg "All prereqs installed - do the following to install stackd.io:"
echo
echo "su - stackdio"
echo "${script_dir}/bootstrap2.sh"
echo
log_msg "#####################################################################"
