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

### Ubuntu: 

    sudo apt-get install mercurial python-pip python-dev libssl-dev libncurses5-dev swig

### CentOS

    sudo yum install python-devel ncurses-devel swig openssl-devel

### Users and paths

    The standard user we'll be using is 'stackdio', so we'll need to create the account:

    useradd -m -s/bin/bash -U stackdio

    We'll be setting everything up in /mnt/stackdio_root. You can change it to
    wherever you'd like, but some of the details below will also need to change
    and most of the defaults won't work without modifying some environment variables
    and settings.

### virtualenv-burrito

###### Install it

    curl -s https://raw.github.com/brainsik/virtualenv-burrito/master/virtualenv-burrito.sh | $SHELL
    
### MySQL

###### Install it:
    
    With Homebrew: brew update && brew install mysql
    
    Ubuntu: sudo apt-get install mysql-server mysql-client libmysqlclient-dev

    CentOS: sudo yum install mysql mysql-server mysql-devel

###### Start the service

    Ubuntu: sudo service mysql start

    CentOS: sudo service mysqld start
    
###### Set up your database and users:

    # start the mysql shell
    mysql -hlocalhost -uroot

    # In mysql shell 
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

    # Clone the source down

    hg clone https://hg.corp.digitalreasoning.com/internal/configuration-management /mnt/stackdio_root

    # Set up some environment variables
    
    The file `/mnt/stackdio_root/postactivate` contains several environment
    variables that need to be exported. You can put these in your stackdio
    users bash_profile or in your stackdio virtual environments
    bin/postactivate file. Be sure to take a look at them and make any 
    appropriate changes and if you don't use virtualenv, make sure to
    source the appropriate file to get the new variables.

    # Initialize your virtualenv

    workon stackdio

    # Install stackd.io's Python dependencies into the virtualenv

    cd /mnt/stackdio_root/stackdio
    pip install -r stackdio/requirements/local.txt

    # NOTE: On CentOS, you'll likely get an error like "This openssl-devel package does not work your architecture"
    # when it starts installing M2Crypto. To fix this, go into your virtual env direct (with
    # virtualenv-wrapper its cdvirtualenv), into the build/M2Crypto and run
    #
    # bash fedora_setup.sh build
    # bash fedora_setup.sh install
    #
    # You will then need to re-run the pip install command above once more.
    
    # If you're running a newer version of Ubuntu, please see the next section
    # before proceeding.
    
    # Initialize the database and start Django's built-in web server
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

    # Symlink the salt states into the right location under our salt_root. 
    ln -s /path/to/stackdsalt /opt/salt_root/srv

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
    http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html#daemonizing

### Unit Tests

We are using the [django-nose] library to utilize the Nose testing framework from within our Django project. At any time, you can execute the tests by running:

    ./manage.py test

### User Interface

The stackd.io framework comes with a default user interface that uses the [Sencha ExtJS] application framework, which, by default, is pre-compiled into the __stackdio/core/static__ directory of the project.

#### Running

To start using it, simply point your browser to:

    http://{ip|host}:{port}/static/index.html

#### Compiling

##### Setting up Sencha Command

If you want to make changes or add to the UI, you need to compile the source code when you are done. By default, the software needed to compile the user interface is not installed when you download the project.

To do this, first, download and install [Sencha Command].

For full documentation on Sencha Command, please visit the [Introduction to Sencha Cmd for ExtJS] page.

##### Compile the Code

From the CLI, in the __stackdui/src__ directory, run the following command:

    sencha app build
    
Once that process is complete, you can refresh your browser and your new code will be live.

### Technology

stackd.io uses a number of open source projects to work properly. For a more up-to-date list of dependencies, please see the requirements.txt file.

* [Django] - the coolest Python web framework around
* [Django REST Framework] - a RESTful API framework for Django
* [South] - a database migration utility for Django's ORM
* [Celery] - asynchronous task queue/job queue based on distributed message passing
* [django-celery] - Django integration for Celery
* [RabbitMQ] - complete and highly reliable enterprise messaging system based on the emerging AMQP standard
* [Sencha ExtJS] - an advanced web application framework

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
  [django-nose]: https://github.com/jbalogh/django-nose
  [Sencha ExtJS]: http://www.sencha.com/products/extjs/
  [Sencha Command]: http://www.sencha.com/products/sencha-cmd/download
  [Introduction to Sencha Cmd for ExtJS]: http://docs.sencha.com/extjs/4.2.1/#!/guide/command
