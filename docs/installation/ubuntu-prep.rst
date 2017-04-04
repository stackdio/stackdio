Preparing Ubuntu for stackd.io installation
===========================================

The steps below were written using Ubuntu 16.04 from a Ubuntu-provided AMI on Amazon Web Services (AWS).
The exact AMI we used is ``ami-29f96d3e``, and you should be able to easily launch an EC2 instance using this AMI from the
`AWS EC2 Console <https://console.aws.amazon.com/ec2/home?region=us-east-1#launchAmi=ami-29f96d3e>`__.

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

    sudo apt-get install postgresql

Below we'll create a ``stackdio`` database and grant permissions to the ``stackdio`` user for that database.

    **WARNING**: we're not focusing on security here, so the default
    Postgres setup definitely needs to be tweaked, passwords changed, etc.,
    but for a quick-start guide this is out of scope.
    Please, don't run this as-is in production.

.. code:: bash

    sudo -u postgres psql postgres <<EOF
    CREATE USER stackdio WITH UNENCRYPTED PASSWORD 'password';
    CREATE DATABASE stackdio;
    ALTER DATABASE stackdio OWNER to stackdio;
    EOF

Core requirements
-----------------

- libpq-dev (the c header files for compiling the python postgres client)
- python-dev (for compiling native python libraries)
- redis-server (for our cache / message queue)
- nginx (for serving static files)

To quickly get up and running, you can run the following to install the
required packages.

.. code:: bash

    # Install requirements needed to install stackd.io
    sudo apt-get install libpq-dev python-dev redis-server nginx

Next Steps
----------

You're now finished with the Ubuntu-specific requirements for stackd.io.
You can head back over to the :ref:`Manual Install <installation>` and continue the installation of stackd.io.
