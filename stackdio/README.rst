# README

stackd.io is a web-based tool for provisioning and managing cloud infrastructure. 

### Team:

For assistance, please see one of the following kind sirs:

 - [Abe Music]
 - [Charlie Penner]
 - [Steve Brownlee]

### PROJECT HISTORY

- v0.1 (08-May-2013)
 - Stuff
 - More stuff

# Developer Installation
***

### Prequisites:

  - Python >= 2.6
  - [MySQL] - we recommend using Homebrew if using OS X
  - [pip]
  - [virtualenv-wrapper] or [pythonbrew]
  - [RabbitMQ] - again, Homebrew is nice
  - [swig] - yup, Homebrew

### MySQL

###### Install it:
    
    With Homebrew: brew update && brew install mysql
    
###### Set up your database and users:

    # In mysql shell
    create database stackdio;
    create user stackdio;
    grant all on stackdio.* to 'stackdio'@'localhost' identified by 'password'
    
    # Note: you can change the user and password, but make sure to set the env
    # variables later to the correct value.
    
    # Note 2: please don't change the database name!

###### Resetting your database (if you need to):

    mysqladmin -uroot drop stackdio;
    mysqladmin -uroot create stackdio;

### stackdio:

###### Create your virtualenv:

    mkvirtualenv stackdio
    workon stackdio

###### Clone and initialize stackdio:
    
    # Set the following environment variables.
    # MYSQL_USER (the user that will connect to the MySQL server @ localhost)
    # MYSQL_PASS (the password for the user above)

    NOTE: If using virtualenv-wrapper it's best to put these in your postactivate
    script as you may be using multiple projects that require the same environment
    variables, but with different values.

    hg clone https://hg.corp.digitalreasoning.com/internal/configuration-management stackdio
    cd stackdio
    sudo pip install -r stackdio/requirements/local.txt
    python manage.py syncdb --noinput
    python manage.py migrate
    python manage.py loaddata local_data
    python manage.py runserver


Point your browser to http://localhost:8000. There are two default users in the system:
 
  * admin / password
  * testuser / password

API endpoints can be found at http://localhost:8000/api/

### Salt & Salt-Cloud

###### Installation:
    
    # Should already be handled by the requirements files. If you're running OS X
    # you have a few more things to do. 
    
    # First, install the curl-ca-bundle for SSL using Homebrew. If you'd rather 
    # not use Homebrew for whatever reason, see 
    # http://libcloud.apache.org/docs/ssl-certificate-validation.html
 
    brew install curl-ca-bundle
 
    # Now, put it in the right spot for libcloud to find it:
 
    mkdir -p /opt/local/share/curl
    cd /opt/local/share/curl
    ln -s /usr/local/share/ca-bundle.crt curl-ca-bundle.crt

###### Configuration:

    # OK, stick with me on this :)
    
    # First, we're going to change the default location of where salt will pull
    # its configuration from (I'm using /opt/salt_root, and you should too :) )
    mkdir -p /opt/salt_root/etc/salt
    mkdir -p /opt/salt_root/srv/salt
    mkdir -p /opt/salt_root/srv/pillar
    
    # Copy in the master configuration file
    cd <stackdio_root_directory>
    cp stackdio/etc/salt-master /opt/salt_root/etc/salt/master
    
    # Edit the master file  to make sure the 'user' parameter is set correctly
    # (in my case it's abe)
    
    # Setting the following environment variables is required. Again, I
    # suggest putting them in your virtualenv's postactivate file:
        
    export SALT_MASTER_CONFIG=/opt/salt_root/etc/salt/master
    export SALT_CLOUD_CONFIG=/opt/salt_root/etc/salt/cloud
    export SALT_CLOUDVM_CONFIG=/opt/salt_root/etc/salt/cloud.profiles
    export SALT_CLOUD_PROVIDERS_CONFIG=/opt/salt_root/etc/salt/cloud.providers

###### Running:
    
    # To start the salt master:
    salt-master
    
    # To run salt-cloud:
    salt-cloud
    
### RabbitMQ

###### Installation

    OS X: brew install rabbitmq
    Ubuntu: apt-get install rabbitmq-server
    CentOS/RHEL: yum install rabbitmq-server

###### Execution

    OS X: rabbitmq-server (use nohup if you want it in the background)
    Ubuntu: service rabbitmq-server start/stop
    CentOS/RHEL: service rabbitmq-server start/stop
    
    * See http://www.rabbitmq.com/relocate.html for useful overrides.
    
### Celery

###### Installation

    # Should already be handled by the requirements files, but just in case:
    pip install celery django-celery
    
###### Configuration

    Nothing to see here (yet)

###### Execution

    # NOTE: Make sure RabbitMQ is running first or else the celery worker
    # won't be able to connect to the broker
    manage.py celery worker -lDEBUG

    # If you want to run it in the background use nohup. While in development
    # I think it's much faster to have it in the foreground so you can just
    # Ctrl+C the process when you need to make changes.

### Technology

stackd.io uses a number of open source projects to work properly. For a more up-to-date list of dependencies, please see the requirements.txt file.

* [Django] - the coolest Python web framework around
* [Django REST Framework] - a RESTful API framework for Django
* [South] - a database migration utility for Django's ORM
* [Celery] - asynchronous task queue/job queue based on distributed message passing
* [django-celery] - Django integration for Celery
* [RabbitMQ] - complete and highly reliable enterprise messaging system based on the emerging AMQP standard
* [Twitter Bootstrap] - great UI boilerplate for modern web apps

  [Abe Music]: https://wiki.corp.digitalreasoning.com/confluence/display/~abe.music
  [Charlie Penner]: https://wiki.corp.digitalreasoning.com/confluence/display/~charlie.penner
  [Steve Brownlee]: https://wiki.corp.digitalreasoning.com/confluence/display/~steve.brownlee
  [Django]: https://www.djangoproject.com/
  [Django REST Framework]: http://django-rest-framework.org/
  [South]: https://github.com/dmishe/django-south
  [Celery]: http://www.celeryproject.org/
  [django-celery]: http://docs.celeryproject.org/en/latest/django/index.html
  [RabbitMQ]: http://www.rabbitmq.com/
  [Twitter Bootstrap]: http://twitter.github.com/bootstrap/
  [pip]: http://www.pip-installer.org/en/latest/
  [virtualenv-wrapper]: https://bitbucket.org/dhellmann/virtualenvwrapper
  [pythonbrew]: https://github.com/utahta/pythonbrew
  [MySQL]: http://dev.mysql.com/downloads/
