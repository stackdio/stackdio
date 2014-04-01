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

# OS-specifc preparation

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

### Create a stackd.io admin user

> **NOTE**: stackd.io can also integrate with an existing LDAP server. See our [LDAP guide](ldap_guide.md) for more information on configuring stackd.io to use your existing LDAP server. If you choose to go the LDAP route, you can skip this entire section because users who successfully authenticate via LDAP will automatically be created in stackd.io.

```bash
stackdio manage.py createsuperuser

# and follow prompts...
```

# stackd.io operations

### Start the development server

For the quick start, we're going to run with Django's built-in web server. In production, you'll definitely want to consider something more appropriate like Apache or Nginx. See [Django's WSGI deployment documentation](https://docs.djangoproject.com/en/1.5/howto/deployment/wsgi/) or check out our [stackd.io webserver guide](webserver_guide.md) for quickly getting stackd.io running behind Apache2 or Nginx.

```bash
stackdio manage.py runserver 0.0.0.0:8000
```

This will run the Django development server in the foreground, meaning you won't be able to do anything else in your current shell while it's running. You will need to either use something like `nohup` to put it in the background or open a new shell (remember to use the `workon` command to activate your virtualenv!)

To use nohup, you can do:

```bash
nohup stackdio manage.py runserver 0.0.0.0:8000 &> webserver.nohup.out &
```

### Start rabbitmq and celery

Asynchronous celery tasks handle most of the heavy-lifting within stackd.io and they depend on rabbitmq-server and celery to be running. Let's start them both:

```bash
# rabbitmq-server
sudo service rabbitmq-server start

# celery
stackdio manage.py celery worker -ldebug -c1
```

Like the Django development server, Celery will also run in the foreground and steal your shell. If you want to run celery in the background, use nohup like above or consider using something better like supervisord. See [Celery's daemonizing documentation](http://docs.celeryproject.org/en/3.0/tutorials/daemonizing.html) for more information.


### Creating additional users

The superuser we created earlier will give us admin access to stackd.io, however, you probably want at least one non-superuser. Point your browser to http://hostname:8000/__private/admin and use the username and password for the super user you created earlier. You should be presented with the Django admin interface. To create additional users, follow the steps below.

* click Users
* click Add user in the top right of the page
* set the username and password of the user and click save
* optionally provide first name, last name, and email address of the user and click save

The newly created users will now have access to stackd.io. Test this by logging out and signing in with one of the non-admin users.

# Next steps

This concludes the quick start. At this point you should have a running stackd.io install, but you may need a bit more help in using the system. You can read through the [stackd.io tutorial](tutorial.md) or watch the [stackd.io screencast](http://stackd.io/tour) to learn a bit more about using the system to manage your cloud infrastructure.
