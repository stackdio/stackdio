Installation Overview
=====================

There are two main options for installation:

Amazon AMI
----------

Reading through long install guides and executing each and every command can be time
consuming and error prone.  If you would rather just run a script to do a lot of this
for you, we have a script to build an AMI for you. Keep in mind that the script
is somewhat opinionated and won't let you make many decisions (you're free to modify
it to suit your needs though!) Here's a list of things it will do:

-  Install all of the necessary stuff (MySQL, python, virtualenv, tons of packages, etc)
-  Create a ``stackdio`` virtualenv at ``/usr/share/stackdio``
-  Install stackdio and its python dependencies
-  Install and configure Nginx
-  Install and configure supervisord to run gunicorn, celery, and salt-master
-  Create an ``admin`` stackdio user

Check it out here: :doc:`ami`


Manual Install
--------------

If you'd rather have a more custom-fitted installation that fits your needs, check out
:doc:`manual` instead.
