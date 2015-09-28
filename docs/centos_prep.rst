Preparing CentOS for stackd.io installation
===========================================

The steps below were written using CentOS 6.4 from a CentOS-provided AMI
on Amazon Web Services (AWS). The exact AMI we used is ``ami-bf5021d6``,
and you should be able to easily launch an EC2 instance using this AMI from the
`AWS Marketplace <https://aws.amazon.com/marketplace/pp/B00DGYP804/ref=sp_mpg_product_title?ie=UTF8&sr=0-4>`__.

Prerequisites
=============

All of the CentOS-provided AMIs have SELinux and iptables enabled. We
disabled both of these to be as straight forward as possible during this
guide. SELinux causes issues that are beyond the scope of the guide, and
we disabled iptables because we leverage EC2's security groups for
firewall access.

iptables
--------

Let's just turn it off for now. Please note, if you're using EC2 or some
other cloud provider that has firewall rules enabled by default, you
will need to configure the particular firewall rules to gain access to
the web server we'll start in the guide. The default port for the
webserver is 8000, so open this port up at a minimum. (Port 22 for SSH
will obviously be needed as well.)

.. code:: bash

    sudo service iptables stop

SELinux
-------

Getting things working using SELinux could be an entirely separate
guide. For our purposes, it's completely out of scope, so we're going to
disable it.

.. note::

    You will be required to restart the machine during this step.

.. code:: bash

    # Edit /etc/sysconfig/selinux and make sure the line beginning
    # with SELINUX looks like:
    SELINUX=disabled
     
    # If it was already disabled you can skip the following, however
    # if you switched the policy from anything other than 'disabled'
    # you need to relabel the filesystem to remove the garbage that
    # SELinux has added. This *requires* a restart to take effect.
    touch /.autorelabel
    reboot
     
    # When the machine is back up, you can confirm SELinux is not
    # running
    >>> selinuxenabled
    >>> echo $?
    >>> 1
     
    # If the output is 1 you're good to go.

EPEL
----

.. code:: bash

    sudo rpm -Uvh http://mirror.steadfast.net/epel/6/i386/epel-release-6-8.noarch.rpm

MySQL
-----

.. note::

    Please skip this section if you are using a different database or
    already have a supported database server running elsewhere.

Install MySQL server:

.. code:: bash

    sudo yum install mysql-server

Start MySQL server:

.. code:: bash

    sudo service mysqld start

Below we'll create a ``stackdio`` database and grant permissions to the
``stackdio`` user for that database.

.. warning::

    We're not focusing on security here, so the default
    MySQL setup definitely needs to be tweaked, passwords changed, etc.,
    but for a quick-start guide this is out of scope. Please, don't run
    this as-is in production :)

.. code:: bash

    echo "create database stackdio; \
    grant all on stackdio.* to stackdio@'localhost' identified by 'password';" | \
    mysql -h localhost -u root

virtualenvwrapper
-----------------

.. code:: bash

    # install the package
    sudo yum install python-virtualenvwrapper

    # Update the user's ~/.bash_profile to enable virtualenvwrapper
    # You're using the stackdio user, right? :)
    echo "source /usr/bin/virtualenvwrapper.sh" >> ~/.bash_profile

    # re-source the .bash_profile
    . ~/.bash_profile

Core requirements
-----------------

-  gcc and other development tools
-  git
-  mysql-devel
-  swig
-  python-devel
-  rabbitmq-server
-  nginx

To quickly get up and running, you can run the following to install the
required packages.

.. code:: bash

    # Install the development tools group
    sudo yum groupinstall "Development Tools"

    # Install the other requirements needed to install stackd.io
    sudo yum install git mysql-devel swig python-devel rabbitmq-server nginx nodejs npm

Next Steps
==========

You're now finished with the CentOS-specific requirements for stackd.io.
You can head back over to the :ref:`Quickstart Guide <installing>` and
continue the installation of stackd.io.
