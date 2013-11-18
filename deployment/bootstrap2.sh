#!/bin/bash -e

# 
# This script starts with a bare CentOS AMI and bootstraps the stackd.io
# virtualenv. At the conclusion of this script you should be able to
# actually install stackd.io in your virtualenv.
#


function log_msg {
    echo "[$(date)] $1"
}

if [ ! -e /etc/redhat-release ]; then
    log_msg "This doesn't appear to be a CentOS/RHEL system, but needs to be"
    exit 1
fi

if [ "$(whoami)" != "stackdio" ]; then 
    log_msg "Must be stackdio to run"
    exit 1
fi

HOSTNAME=$(curl http://169.254.169.254/latest/meta-data/public-hostname)
log_msg "#####################################################################"
log_msg " Bootstrapping stackd.io installation (part 2)"
log_msg " CentOS Version  :  $(cat /etc/redhat-release)"
log_msg " Hostname        : $HOSTNAME"
log_msg "#####################################################################"

curl -s https://raw.github.com/brainsik/virtualenv-burrito/master/virtualenv-burrito.sh | $SHELL

sudo yum install -y python-virtualenvwrapper
rm -f $HOME/.venvburrito/bin/virtualenvwrapper.sh
ln -s /usr/bin/virtualenvwrapper.sh $HOME/.venvburrito/bin/virtualenvwrapper.sh
cat >> $HOME/.bash_profile <<EOF
export WORKON_HOME=$HOME/.virtualenvs
source /usr/bin/virtualenvwrapper.sh
EOF
source $HOME/.bash_profile
source $HOME/.venvburrito/startup.sh

log_msg "Installing stackd.io"

set +e
mkvirtualenv stackdio
set -e

VENV_HOME="$HOME/.virtualenvs/stackdio"

echo
log_msg "####"
log_msg "#### ATTENTION:"
log_msg "#### You will be prompted momentarily for your HG username/password."
log_msg "####"
echo

sudo hg clone https://hg.corp.digitalreasoning.com/internal/configuration-management /mnt/stackdio_root
sudo chown -R stackdio:stackdio /mnt/stackdio_root
cd /mnt/stackdio_root/stackdio
hg up 0.5.x
export PATH=$VENV_HOME/bin:$PATH
set +e
pip install -r stackdio/requirements/local.txt
set -e

log_msg "Assuming that the above will break, doing some manual intervention"
cd $VENV_HOME
cd build/M2Crypto
bash fedora_setup.sh build
bash fedora_setup.sh install

cd /mnt/stackdio_root/stackdio
pip install -r stackdio/requirements/local.txt

cat /mnt/stackdio_root/postactivate >> $VENV_HOME/bin/postactivate
source $VENV_HOME/bin/postactivate

num_vars=$(cat $VENV_HOME/bin/postactivate | grep "export " | wc -l)
cnt=1
SUPERVISOR_ENV=$(for ff in $(cat $VENV_HOME/bin/postactivate | \
    grep "export " | awk '{print $2}'); do \
    echo -n "$ff"; \
    if [ $cnt -lt $num_vars ]; then echo -n ","; fi; cnt=$((cnt+1)); done)

# semi-wonky python workaround since sed doesn't like all the $ signs
echo $SUPERVISOR_ENV | sudo python -c "import sys;e=sys.stdin.read().strip();f=open('/etc/supervisord.conf').read();n=f.replace('ENVIRONMENT',e);print(n);open('/etc/supervisord.conf','w').write(n)"

python manage.py syncdb --noinput
python manage.py migrate
python manage.py loaddata local_data
python manage.py collectstatic --noinput

sudo touch /var/log/supervisord.log
sudo chown stackdio:stackdio /var/log/supervisord.log
${VENV_HOME}/bin/supervisord

log_msg "#####################################################################"
log_msg " Bootstrapping is complete, services should be running, you can"
log_msg " logout of this server now."
log_msg "#####################################################################"


