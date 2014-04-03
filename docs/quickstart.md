# Quick Start Guide

This guide is intended to quickly march you through the steps of installing and running stackd.io and its dependencies. We're not intending to be complete or provide you with everything needed for a production-ready install, we may make some assumptions you don't agree with, and there may be things we missed. If you feel anything is out of the ordinary, a bit confusing, or just plain missing, please [contact us](../README.md).

### MySQL

We're using stackd.io internally with MySQL. Since stackd.io is using Django, it inherently supports many different database servers, so if you need something different feel free, but you're on your own for its install. Be sure to plug in the correct settings later when configuring stackd.io with different servers. For more information on Django's database support, see: https://docs.djangoproject.com/en/1.5/ref/databases/

### Python virtual environments

It's highly recommend to install stackd.io into a Python virtualenv, and we recommend using virtualenv wrapper.

# stackd.io user and sudo access

Some of the coming steps in the Quick Start Guide require sudo/root access, but once those are handled, the rest of stackd.io should work with a non-root user. For ease of use, we're going to create a `stackdio` user, give sudo access, and use this user for the remainder of this guide.

```bash
# Create the user
sudo useradd -m -s/bin/bash -U stackdio

# Give sudo
sudo echo 'stackdio ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/stackdio > /dev/null

# Switch to user...and remain as this user for the rest of the guide
sudo su - stackdio
```

# OS-specific preparation

> :warning:       **WARNING**       :warning:
> 
> You must follow the steps in one of the following prep guides for the OS you're installing stackd.io in.

Follow one of the individual guides below to prepare your particular environment for stackd.io. Once you finish, come back here and continue on.

* [Preparing CentOS for stackd.io installation](centos_prep.md)
* [Preparing Ubuntu for stackd.io installation](ubuntu_prep.md)

# Installing stackd.io

Below we're going to create our virtualenv named `stackdio` and install it directy from github. You can name your virtualenv whatever you like, but remember to modify the steps accordingly.

### Creating the virtualenv

Let's create a virtualenv to install stackd.io into:

```bash
mkvirtualenv stackdio
```

The virtualenv should automatically activate when you create it. If you exit your current shell and come back later to work on stackdio and find things not working as expected you probably need to activate the virtualenv again. To do this, virtualenvwrapper gives you the `workon` command:

```bash
workon stackdio
```

### Install the stackd.io project

> **NOTE** Double-check that your virtualenv is activated or else this will probably complain that you don't have permissions to install (because it's trying to install into the global python site-packages directory which we don't want!)

```bash
pip install https://github.com/digitalreasoning/stackdio.git

# The above should install directly from github, but if
# you'd rather install manually:

cd /tmp
git clone git@github.com:digitalreasoning/stackdio.git
cd stackdio
pip install .
```

### Configuration

After the install, you'll have a `stackdio` command available to interact with much of the platform. First off, we need to configure stackd.io a bit. The `stackdio init` command will prompt you for several pieces of information. If you followed all steps above verbatim, then all defaults may be accepted, but if you deviated from the path you will need to provide the following information:

* an existing user on the system that will run everything (it will default to the `stackdio` user)
* an existing location where stackd.io can store its data (the default is `$HOME/.stackdio/storage` and will be created for you if permissions allow)
* a database DSN that points to a running database you have access to (if you're using the MySQL install from above, the default `mysql://stackdio:password@localhost:3306/stackdio` is appropriate)

```bash
stackdio init
```

Now, let's populate are database with a schema:

```bash
stackdio manage.py syncdb --noinput
stackdio manage.py migrate
```

# stackd.io users

### LDAP

stackd.io can easily integrate with an LDAP server. See our [LDAP guide](ldap_guide.md) for more information on configuring stackd.io to work with LDAP. If you choose to go the LDAP route, you can skip this entire section because users who successfully authenticate and are members of the right groups via LDAP will automatically be created in stackd.io.

### Non-LDAP admin user

Admin users in stackd.io have less restriction to various pieces of the platform. For example, only admin users are allowed to create and modify cloud providers and profiles that other users can use to spin up their stacks. 

> NOTE: You will need at least one admin user to configure some key areas of the system.

```bash
stackdio manage.py createsuperuser

# and follow prompts...
```

### Non-LDAP regular users

When not using LDAP, the easiest way to create new non-admin users is to use the built-in Django admin interface. First we need the server to be up and running so keep following the steps below and we'll come back to adding users later.

# Web server configuration

For the quickstart, walk through configuring Nginx to serve our static content as well as proxying the Python app through gunicorn. The required packages should have already been installed during the OS-specific guides above. A couple steps are OS-specific, but we'll call those out below.

The `stackdio` command has a config option that can generate simple configuration for Nginx and Apache2. Here we'll use the nginx generated configuration and store it in the appropriate location.

To configure Nginx for CentOS:

```bash
# CENTOS
stackdio config nginx | sudo tee /etc/nginx/conf.d/stackdio.conf > /dev/null

# rename the default server configuration
sudo mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak
```

To configure Nginx for Ubuntu:

```bash
# UBUNTU ONLY
stackdio config nginx | sudo tee /etc/nginx/sites-available/stackdio.conf > /dev/null
sudo ln -s /etc/nginx/sites-available/stackdio.conf /etc/nginx/sites-enabled

# remove the default configuration symlink
sudo rm /etc/nginx/sites-enabled/default
```

and finally, start Nginx:

```bash
sudo service nginx restart
```

# Rabbitmq, celery, and salt

Start the rabbitmq server:


```bash
sudo service rabbitmq-server start
```

For celery and salt-master, we'll be using supervisord. The required packages should already be installed, so we'll just need to configure supervisor and start the services.

# Creating additional users

> NOTE: If you're using LDAP, you can skip this step.

The superuser we created earlier will give us admin access to stackd.io, however, you probably want at least one non-superuser. Point your browser to http://hostname:8000/__private/admin and use the username and password for the super user you created earlier. You should be presented with the Django admin interface. To create additional users, follow the steps below.

* click Users
* click Add user in the top right of the page
* set the username and password of the user and click save
* optionally provide first name, last name, and email address of the user and click save

The newly created users will now have access to stackd.io. Test this by logging out and signing in with one of the non-admin users.

# Next steps

This concludes the quick start. At this point you should have a running stackd.io install, but you may need a bit more help in using the system. You can read through the [stackd.io tutorial](tutorial.md) or watch the [stackd.io screencast](http://stackd.io/tour) to learn a bit more about using the system to manage your cloud infrastructure.
