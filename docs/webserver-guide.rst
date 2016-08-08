Webserver Guide
===============

This guide will help you quickly get the web portion of stackd.io
running behind Nginx.  **Seeing as stackd.io is just a wsgi app, you
can also run it behind apache using mod_wsgi if you'd like, but
that is beyond the scope of this guide.**  You should've already worked
through this manual install guide before running through
the steps below. As with this guide, our focus is not entirely on
building out a production-ready system, but merely helping you quickly
get a system stood up to become familiar with stackd.io. Once you
understand how it works, then we can start hardening the system for
production use.

Common Steps
------------

To do some of the steps below you will need to have already installed
stackdio and be in the virtual environment. To make sure you're in the
virtualenv:

.. code:: bash

    workon stackdio

Nginx needs a place to store logs and some static files to serve up.
This step should be run before proceeding with configuring Nginx.

.. code:: bash

    # And tell Django to collect its static files into a common directory for the webserver to serve up
    stackdio manage.py collectstatic --noinput


In our configuration, Nginx will be used to serve static files and as a
proxy to send requests down to the Django application running via
gunicorn on port 8000. The configuration we'll generate is useful to use
a quick start mechanism to get you up and running behind Nginx/gunicorn
very quickly.

CentOS Installation
-------------------

Install required packaged, generate and write configuration file, and
restart server:

.. code:: bash

    sudo yum install nginx

    stackdio config nginx | sudo tee /etc/nginx/conf.d/stackdio.conf > /dev/null

    # rename the default server configuration
    sudo mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak

    sudo service nginx restart

Ubuntu Installation
-------------------

.. code:: bash

    sudo apt-get install nginx

    stackdio config nginx | sudo tee /etc/nginx/sites-enabled/stackdio.conf > /dev/null

    # remove the default configuration symlink
    sudo rm /etc/nginx/sites-enabled/default

    sudo service nginx restart
