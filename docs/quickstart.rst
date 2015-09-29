Quick Start Guide
=================

This guide is intended to quickly march you through the steps of
installing and running stackd.io and its dependencies. We're not
intending to be complete or provide you with everything needed for a
production-ready install, we may make some assumptions you don't agree
with, and there may be things we missed. If you feel anything is out of
the ordinary, a bit confusing, or just plain missing, please :doc:`contact
us<contact>`.

Quick Start Script
------------------

We know that reading through a big, messy guide like this one and
executing each and every command will be time consuming and error prone.
If you would rather just run a script to do a lot of this for you, we
have a script for just that. Keep in mind that the script is somewhat
opinionated and won't let you make many decisions (you're free to modify
it to suit your needs though!) Here's a list of things it will do:

-  Detect your OS (only Ubuntu 13.10 and CentOS 6.4 were tested)
-  Install all of the necessary stuff (MySQL, virtualenv-wrapper, tons
   of packages, etc)
-  Create a ``stackdio`` virtualenv
-  Install stackdio and its python dependencies
-  Install and configure Nginx
-  Install and configure supervisord to run gunicorn, celery, and
   salt-master

If you're cool with this, download the script located in
``scripts/stackdio_quickstart.sh`` and execute it on a server as a user
with sudo access.

MySQL
-----

We're using stackd.io internally with MySQL. Since stackd.io is using
Django, it inherently supports many different database servers, so if
you need something different feel free, but you're on your own for its
install. Be sure to plug in the correct settings later when configuring
stackd.io with different servers. For more information on Django's
database support, see:
https://docs.djangoproject.com/en/1.8/ref/databases/

Python virtual environments
---------------------------

It's highly recommend to install stackd.io into a Python virtualenv, and
we recommend using virtualenv wrapper.

stackdio user and sudo access
-----------------------------

Some of the coming steps in the Quick Start Guide require sudo/root
access, but once those are handled, the rest of stackd.io should work
with a non-root user. For ease of use, we're going to create a
``stackdio`` user, give sudo access, and use this user for the remainder
of this guide.

.. code:: bash

    # Create the user
    sudo useradd -m -s/bin/bash -U stackdio

    # Give sudo
    sudo echo 'stackdio ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/stackdio > /dev/null

    # Switch to user...and remain as this user for the rest of the guide
    sudo su - stackdio

OS-specific preparation
-----------------------

.. warning::

    You must follow the steps in one of the following prep guides for
    the OS you're installing stackd.io in.

Follow one of the individual guides below to prepare your particular
environment for stackd.io. Once you finish, come back here and continue
on.

-  :doc:`centos-prep`
-  :doc:`ubuntu-prep`

.. _installation:

Installation
------------

Below we're going to create our virtualenv named ``stackdio`` and
install it directy from github. You can name your virtualenv whatever
you like, but remember to modify the steps accordingly.

Creating the virtualenv
~~~~~~~~~~~~~~~~~~~~~~~

Let's create a virtualenv to install stackd.io into:

.. code:: bash

    mkvirtualenv stackdio

The virtualenv should automatically activate when you create it. If you
exit your current shell and come back later to work on stackdio and find
things not working as expected you probably need to activate the
virtualenv again. To do this, virtualenvwrapper gives you the ``workon``
command:

.. code:: bash

    workon stackdio

Install bower
~~~~~~~~~~~~~

In your terminal, run the following command to install bower:

.. note::

    You must have previously installed npm/node from the OS specific preparation

.. code:: bash

    sudo npm install -g bower

Install the stackd.io project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    Double-check that your virtualenv is activated or else this
    will probably complain that you don't have permissions to install
    (because it's trying to install into the global python site-packages
    directory which we don't want!)

There's two options for installing here.  We recommend pulling the latest version from our
`releases page <https://github.com/stackdio/stackdio/releases>`__, like this:

.. code:: bash

    workon stackdio  # Activate the virtualenv
    pip install https://github.com/stackdio/stackdio/releases/download/0.7.0a4/stackdio_server-0.7.0a4-py2-none-any.whl

If you'd rather have the most up to date code, you can install from our develop branch:

.. code:: bash

    workon stackdio  # Activate the virtualenv
    cd /tmp
    git clone https://github.com/stackdio/stackdio.git
    cd stackdio
    bower install
    pip install .

Configuration
-------------

After the install, you'll have a ``stackdio`` command available to
interact with much of the platform. First off, we need to configure
stackd.io a bit. The ``stackdio init`` command will prompt you for
several pieces of information. If you followed all steps above verbatim,
then all defaults may be accepted, but if you deviated from the path you
will need to provide the following information:

-  an existing user on the system that will run everything (it will
   default to the ``stackdio`` user)
-  an existing location where stackd.io can store its data (the default
   is ``$HOME/.stackdio/storage`` and will be created for you if
   permissions allow)
-  a database DSN that points to a running database you have access to
   (if you're using the MySQL install from above, the default
   ``mysql://stackdio:password@localhost:3306/stackdio`` is appropriate)

.. code:: bash

    stackdio init

Now, let's populate are database with a schema:

.. code:: bash

    stackdio manage.py migrate

**IF** you installed from our github repository, you'll need to build the minified javascript files:

.. code::

    # ONLY DO THIS IF YOU INSTALLED FROM THE GITHUB REPOSITORY.
    stackdio manage.py build_ui


stackd.io users
---------------

LDAP
~~~~

stackd.io can easily integrate with an LDAP server. See our :doc:`ldap-guide`
for more information on configuring stackd.io to work with LDAP.
If you choose to go the LDAP route, you can skip this
entire section because users who successfully authenticate and are
members of the right groups via LDAP will automatically be created in
stackd.io.

Non-LDAP admin user
~~~~~~~~~~~~~~~~~~~

Admin users in stackd.io have less restriction to various pieces of the
platform. For example, only admin users are allowed to create and modify
cloud providers and profiles that other users can use to spin up their
stacks.

.. note::

    You will need at least one admin user to configure some key areas of the system.

.. code:: bash

    stackdio manage.py createsuperuser

    # and follow prompts...

Non-LDAP regular users
~~~~~~~~~~~~~~~~~~~~~~

When not using LDAP, the easiest way to create new non-admin users is to
use the built-in Django admin interface. First we need the server to be
up and running so keep following the steps below and we'll come back to
adding users later.

Web server configuration
------------------------

For the quickstart, we'll use the ``stackdio`` command to generate the
necessary configuration for Nginx to serve our static content as well as
proxying the Python app through gunicorn.

To configure Nginx for CentOS:

.. code:: bash

    # CENTOS

    # add execute permissions to the user's home directory for static content to serve correctly
    chmod +x ~/

    stackdio config nginx | sudo tee /etc/nginx/conf.d/stackdio.conf > /dev/null

    # rename the default server configuration
    sudo mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak

To configure Nginx for Ubuntu:

.. code:: bash

    # UBUNTU ONLY
    stackdio config nginx | sudo tee /etc/nginx/sites-available/stackdio > /dev/null
    sudo ln -s /etc/nginx/sites-available/stackdio /etc/nginx/sites-enabled

    # remove the default configuration symlink
    sudo rm /etc/nginx/sites-enabled/default

After this, generate the static content we'll need to serve:

.. code:: bash

    stackdio manage.py collectstatic --noinput

and finally, start Nginx:

.. code:: bash

    sudo service nginx restart

RabbitMQ, celery, and salt
--------------------------

Start the rabbitmq server:

.. code:: bash

    sudo service rabbitmq-server start

For celery and salt-master, we'll be using supervisord. The required
packages should already be installed, so we'll just need to configure
supervisor and start the services.

.. code:: bash


    # generate supervisord configuration that controls gunicorn, celery, and salt-master and store it in the .stackdio directory.
    stackdio config supervisord > ~/.stackdio/supervisord.conf

    # launch supervisord and start the services
    supervisord -c ~/.stackdio/supervisord.conf
    supervisorctl -c ~/.stackdio/supervisord.conf start all

Try it out!
-----------

At this point, you should have everything configured and running, so
fire up a web browser and point it to your hostname and you should see
the stackd.io login page. If you're using LDAP, try logging in with a
user that is a member of the ``stackdio-admin`` and ``stackdio-user``
groups, or login with the admin user you created earlier.

Creating additional users
-------------------------

.. note::

    If you're using LDAP, you can skip this step.

The superuser we created earlier will give us admin access to stackd.io,
however, you probably want at least one non-superuser. Point your
browser to http://hostname:8000/__private/admin and use the username and
password for the super user you created earlier. You should be presented
with the Django admin interface. To create additional users, follow the
steps below.

-  click Users
-  click Add user in the top right of the page
-  set the username and password of the user and click save
-  optionally provide first name, last name, and email address of the
   user and click save

The newly created users will now have access to stackd.io. Test this by
logging out and signing in with one of the non-admin users.
