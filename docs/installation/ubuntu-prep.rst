Preparing Ubuntu for stackd.io installation
===========================================

The steps below were written using Ubuntu 13.10 from a Ubuntu-provided AMI on Amazon Web Services (AWS).
The exact AMI we used is ``ami-2f252646``, and you should be able to easily launch an EC2 instance using this AMI from the
`AWS EC2 Console <https://console.aws.amazon.com/ec2/home?region=us-east-1#launchAmi=ami-2f252646>`__.

Prerequisites
-------------

All of these steps require ``root`` or ``sudo`` access.
Before installing anything with ``apt-get`` you should run ``apt-get update`` first.

Postgres
--------

.. note::

    Please skip this section if you are using a different
    database or already have a supported database server running
    elsewhere.

Install Postgres server:

.. code:: bash

    sudo apt-get install postgresql-server

Below we'll create a ``stackdio`` database and grant permissions to the ``stackdio`` user for that database.

    **WARNING**: we're not focusing on security here, so the default
    MySQL setup definitely needs to be tweaked, passwords changed, etc.,
    but for a quick-start guide this is out of scope. Please, don't run
    this as-is in production :)

.. code:: bash

    echo "create database stackdio; \
    grant all on stackdio.* to stackdio@'localhost' identified by 'password';" | \
    psql -u root

virtualenvwrapper
-----------------

.. code:: bash

    # install the package
    sudo apt-get install virtualenvwrapper

    # post-install step for virtualenvwrapper shortcuts
    source /etc/bash_completion.d/virtualenvwrapper

Core requirements
-----------------

-  gcc and other development tools
-  git
-  postgres-devel
-  swig
-  python-devel
-  redis-server

To quickly get up and running, you can run the following to install the
required packages.

.. code:: bash

    # Install requirements needed to install stackd.io
    sudo apt-get install python-dev libssl-dev libncurses5-dev libyaml-dev swig nodejs npm \
        libpsqlclient-dev redis-server git nginx libldap2-dev libsasl2-dev

.. code:: bash

    # Link nodejs over to node - bower will complain otherwise
    sudo ln -s /usr/bin/nodejs /usr/bin/node

Next Steps
----------

You're now finished with the Ubuntu-specific requirements for stackd.io.
You can head back over to the :ref:`Manual Install <installation>` and continue the installation of stackd.io.
