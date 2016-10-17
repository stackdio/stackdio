Welcome to stackd.io!
=====================

stackd.io is a modern cloud deployment and provisioning framework for everyone.
Its purpose is to provide a common platform for deploying and configuring hardware on **any** cloud platform.
We currently only support AWS EC2, but the driver framework is expandable to support other cloud providers.

stackd.io is built on top of `Django`_.
We currently use `salt-cloud`_ to build infrastructure, and `salt`_ to orchestrate that infrastructure.

.. _Django: https://www.djangoproject.com/
.. _salt: http://saltstack.com/
.. _salt-cloud: https://docs.saltstack.com/en/latest/topics/cloud/

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