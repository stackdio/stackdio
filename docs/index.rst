Welcome to stackd.io!
=====================

stackd.io is a modern cloud deployment and provisioning framework for everyone.  Its purpose
is to provide a common platform for deploying and configuring hardware on **any** cloud platform.
We currently only support AWS EC2, but the driver framework is expandable to support other
cloud providers.

stackd.io is a `Django`_ project, and uses `Salt`_ for its back-end configuration management.

.. _Django: https://www.djangoproject.com/
.. _Salt: http://saltstack.com/

.. toctree::
   :maxdepth: 1
   :caption: Installation Guide

   installation/overview
   installation/manual
   installation/ami
   installation/ldap-guide


.. toctree::
   :maxdepth: 1
   :caption: Concepts


.. toctree::
   :maxdepth: 1
   :caption: User Guide

   webserver-guide
   contact


.. toctree::
   :maxdepth: 1
   :caption: Developer Guide

   developers/contributor-guide