Overview
========

| This directory contains several resources for deploying stackd.io in a
| production environment. If you are doing development of stackd.io,
  these
| resources will still be valuable, but you may want to tweak various
  aspects to
| best fit your needs.

| The end goal of these resources is for you to be able to fire up your
  browser,
| and immediately start using stackd.io in your EC2 environment.

Prerequisites
=============

| While stackd.io itself is not tied to any particular OS or
  configuration, these
| specific deployment resources are designed for/limited to the
  following:

-  `AWS EC2 <http://aws.amazon.com>`__
-  `CentOS <https://www.centos.org>`__

Tooling used to deploy:

-  `AWS Command Line Interface <http://aws.amazon.com/cli/>`__
-  bash

| You will need to create a `key
  pair <http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html>`__
  and `security
  group <http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html>`__
  in your AWS
| account before being able to start anything here. At a minimum you
  will need
| to open ports 22 and 80 to whatever IP addresses you would like to
  have access
| to.

Bootstrapping
=============

| To get started, execute ``instance_launch.sh`` to launch a bare
  `CentOS AMI <https://aws.amazon.com/marketplace/pp/B00A6KUVBW/>`__
| that's suitable for deploying stackd.io:

::

    instance_launch.sh KEYPAIR_NAME SECURITY_GROUP

| When the instance is ready this will upload the bootstrapping content
  and log
| you into the instance, where you'll run:

::

    /tmp/deployment/bootstrap1.sh

| The first script (``bootstrap1.sh``) must be run as the ``root`` user,
  and will
| install all of the prerequisites for stackd.io. Once it is complete,
  you will
| need to ``su`` to the newly created ``stackdio`` user to continue:

::

    su - stackdio
    /tmp/deployment/bootstrap2.sh

| **NOTE** that stackd.io is currently hosted on a private Mercurial
  repository,
| and you will be prompted for a username/password during the execution
  of
| ``bootstrap2.sh``.

Starting and Using
==================

| Once the bootstrap scripts finish, you should have all services
  necessary for
| accessing and using stackd.io. Most services are controlled via
| `supervisord <http://supervisord.org>`__, with a few exceptions that
  are managed by the init.d/service
| scripts. To restart any of the supervisor processes use
  ``supervisorctl``. For
| example to restart Django:

::

    > supervisorctl
    celery-main                      RUNNING    pid 28642, uptime 0:00:02
    celery-formulas                  RUNNUNG    pid 28644, uptime 0:00:02
    gunicorn-django                  RUNNING    pid 28643, uptime 0:00:01
    salt-master                      RUNNING    pid 28645, uptime 0:00:04
    supervisor> restart gunicorn-django

| Note that `supervisord <http://supervisord.org>`__ is **not** a
  requirement for using stackd.io, however
| it does provide an easy to use resilient method of keeping everything
  running
| properly. You may use whatever process management system you prefer to
  operate
| stackd.io.

| To start using stackd.io, simply go to http://EC2-HOSTNAME in your
  browser, and
| login with the default admin user/password: ``admin``/``password``.
  The REST API
| is browsable at http://EC2-HOSTNAME/api.

An Important Caveat
===================

| While this is configured robustly with `nginx <http://nginx.org>`__,
  SSL is not included here.
| However it is **strongly** recommended that you secure your stackd.io
  installation
| with SSL. See the `nginx
  ssl <http://nginx.org/en/docs/http/ngx_http_ssl_module.html>`__ docs
  for details on how to configure this, or
| you may choose to use a different web server.
