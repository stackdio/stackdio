# README

stackd.io is a web-based tool for provisioning and managing cloud infrastructure. 

### Team:

For assistance, please see one of the following Dintinguished Gentlemen:

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

  - Python >= 2.6 (with development headers)
  - [MySQL] - we recommend using Homebrew if using OS X
  - [pip]
  - [virtualenv-burrito] or [pythonbrew]
  - [RabbitMQ] - again, Homebrew is nice
  - [swig] - yup, Homebrew

### Ubuntu stuff

    sudo apt-get install mercurial python-pip python-dev libssl-dev libncurses5-dev

### virtualenv-burrito

###### Install it

    curl -s https://raw.github.com/brainsik/virtualenv-burrito/master/virtualenv-burrito.sh | $SHELL
    
### Swig

###### Install it

    Homebrew: brew install swig
    
    Ubuntu: sudo apt-get install swig

### MySQL

###### Install it:
    
    With Homebrew: brew update && brew install mysql
    
    Ubuntu: sudo apt-get install mysql-server mysql-client libmysqlclient-dev
    
###### Set up your database and users:

    # In mysql shell (hint: run `mysql`)
    create database stackdio;
    create user stackdio;
    grant all on stackdio.* to 'stackdio'@'localhost' identified by 'password';
    
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
    
    # Set the django secret key environment variable. For development purposes
    # this can be just about anything, but when in production, choose something
    # very, very hard to guess - random gibberish is mostly preferred :)
    export DJANGO_SECRET_KEY='randomgibberishgobbeltygook'
    
    # Set the following environment variables for MySQL
    export MYSQL_USER='stackdio'
    export MYSQL_PASS='password'
    
    # Setting the following environment variables is also required. Again, I
    # suggest putting them in your virtualenv's postactivate file. These are
    # so Django and celery tasks know where to get to salt configuration and
    # scripts. We won't be installing salt or salt cloud for a bit, but go
    # ahead and set them.
        
    export SALT_ROOT=/opt/salt_root
    export SALT_MASTER_CONFIG=/opt/salt_root/etc/salt/master
    export SALT_CLOUD_CONFIG=/opt/salt_root/etc/salt/cloud
    export SALT_CLOUDVM_CONFIG=/opt/salt_root/etc/salt/cloud.profiles
    export SALT_CLOUD_PROVIDERS_CONFIG=/opt/salt_root/etc/salt/cloud.providers

    NOTE: If using virtualenv-wrapper it's best to put these in your postactivate
    script as you may be using multiple projects that require the same environment
    variables, but with different values.
    
    # Reinitialize your virtualenv to get those new environment variables
    workon stackdio

    hg clone https://hg.corp.digitalreasoning.com/internal/configuration-management stackdio_root
    cd stackdio_root/stackdio
    pip install -r stackdio/requirements/local.txt
    
    # If you're running a newer version of Ubuntu, please see the next section
    # before proceeding.
    
    python manage.py syncdb --noinput
    python manage.py migrate
    python manage.py loaddata local_data
    python manage.py runserver 0.0.0.0:8000
    
###### Ubuntu has some issues with SSLV2

    Ubuntu doesn't ship a Python version that includes SSLV2, which M2Crypto
    depends on, so a bit of magic needs to happen. Taken from
    https://raw.github.com/Motiejus/django-webtopay/master/m2crypto_ubuntu
    
    # First remove M2Crypto
    pip uninstall M2Crypto
    
    cd /tmp
    touch foo.sh
    
    # Next, copy bash script below to /tmp/foo.sh and run it
    bash /tmp/foo.sh
    
    #!/bin/sh -xe
    
    # Sets up m2crypto on ubuntu architecture in virtualenv
    # openssl 1.0 does not have sslv2, which is not disabled in m2crypto
    # therefore this workaround is required
    
    PATCH="
    --- SWIG/_ssl.i 2011-01-15 20:10:06.000000000 +0100
    +++ SWIG/_ssl.i 2012-06-17 17:39:05.292769292 +0200
    @@ -48,8 +48,10 @@
     %rename(ssl_get_alert_desc_v) SSL_alert_desc_string_long;
     extern const char *SSL_alert_desc_string_long(int);
    
    +#ifndef OPENSSL_NO_SSL2
     %rename(sslv2_method) SSLv2_method;
     extern SSL_METHOD *SSLv2_method(void);
    +#endif
     %rename(sslv3_method) SSLv3_method;
     extern SSL_METHOD *SSLv3_method(void);
     %rename(sslv23_method) SSLv23_method;"
    
    pip install --download="." m2crypto
    tar -xf M2Crypto-*.tar.gz
    rm M2Crypto-*.tar.gz
    cd M2Crypto-*
    echo "$PATCH" | patch -p0
    python setup.py install

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
    
    # Copy in the master and cloud configuration files for defaults
    cd <stackdio_root_directory>
    cp stackdio/etc/salt-master /opt/salt_root/etc/salt/master
    cp stackdio/etc/salt-cloud /opt/salt_root/etc/salt/cloud
    
    # Edit the master file  to make sure the 'user' parameter is set correctly. It
    # should be the user that Django, celery, and salt will all run as (on my box
    # it's abe, but if you're in EC2 it may be ubuntu or ec2-user or anything else
    # as long as you're using that user)
    
    # The cloud file should be ready to go as there's not much going on, but if
    # you can change the default log directory, just make sure the path exists
    # and the user running salt-cloud has the right permissions.

###### Running:
    
    # To start the salt master:
    salt-master
    
    # To run salt-cloud:
    salt-cloud
    
### RabbitMQ

###### Installation

    OS X: brew install rabbitmq
    
    Ubuntu: sudo apt-get install rabbitmq-server

###### Execution

    OS X: rabbitmq-server (use nohup if you want it in the background)
    
    Ubuntu: service rabbitmq-server start/stop
    
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

    # See celery documentation for ways of daemonizing the process

### User Interface

The stackd.io framework comes with a default user interface that uses the Node.js-based Meteor framework. For full documentation, please visit 

    http://docs.meteor.com/#quickstart

#### Installation

You can install Meteor by executing the following command.

    curl https://install.meteor.com | /bin/sh
    
#### Django CORS configuration

In order to access the API running on port 8000, you need to enable CORS access in Django. Do do this, uncomment the corsheader middleware statement in the __settings/base.py__ file.

    # 'corsheaders.middleware.CorsMiddleware',
    
Then uncomment the CORS whitelist setting. Search for 'whitelist' and you'll find it.

    # CORS_ORIGIN_WHITELIST = (
    #    'localhost:3000',
    # )

Obviously, this has to match the port on which the Meteor process is running. If you start Meteor on a different port, reflect that change in the whitelist.

#### Running

To start the user interface, simply run meteor in the tooling directory. This will start a Node server on port 3000.

    cd tooling
    meteor
    
Then open your browser and start the initial setup

    http://localhost:3000/

### Technology

stackd.io uses a number of open source projects to work properly. For a more up-to-date list of dependencies, please see the requirements.txt file.

* [Django] - the coolest Python web framework around
* [Django REST Framework] - a RESTful API framework for Django
* [South] - a database migration utility for Django's ORM
* [Celery] - asynchronous task queue/job queue based on distributed message passing
* [django-celery] - Django integration for Celery
* [RabbitMQ] - complete and highly reliable enterprise messaging system based on the emerging AMQP standard
* [Twitter Bootstrap] - great UI boilerplate for modern web apps
* [Meteor] - An open-source platform for building real-time, top-quality web apps

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
  [Meteor]: http://www.meteor.com
  [pip]: http://www.pip-installer.org/en/latest/
  [virtualenv-burrito]: https://github.com/brainsik/virtualenv-burrito
  [pythonbrew]: https://github.com/utahta/pythonbrew
  [MySQL]: http://dev.mysql.com/downloads/
