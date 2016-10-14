Using the Amazon AMI
====================

To make installation easier, we provide an `packer`_ build that creates an Amazon Machine Image (AMI).
This AMI is built from an Ubuntu 14.04 LTS image, and is HVM based.
While our ultimate plan is to provide this AMI on the `AWS Marketplace`_, we don't have this set up yet.


Building an AMI
---------------

.. note::

    The build script that runs packer requires you to have python installed locally.

1. Install Packer
~~~~~~~~~~~~~~~~~

If you haven't already, install packer using their documentation `here <https://packer.io/docs/installation.html>`_.
We recommend using homebrew for the installation if you're using OSX.


2. Accept License
~~~~~~~~~~~~~~~~~

Before building with packer, you must accept the license agreement for the base Ubuntu AMI:
http://aws.amazon.com/marketplace/pp?sku=b3dl4415quatdndl4qa6kcu45


3. Clone Repository
~~~~~~~~~~~~~~~~~~~

.. code:: bash

    git clone https://github.com/stackdio/stackdio.git
    cd stackdio


4. Export AWS Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure packer knows about your aws credentials:

.. code:: bash

    export AWS_ACCESS_KEY='<YOUR_ACCESS_KEY>'
    export AWS_SECRET_KEY='<YOUR_SECRET_KEY>'


5. Run the packer build
~~~~~~~~~~~~~~~~~~~~~~~

Finally, run the packer build, where ``<version>`` is the version you want to build:

.. code:: bash

    ./packer/build.py <version>


After a few minutes, you should have a usable AMI.


Using the AMI
-------------

After you've built the AMI, you can launch an instance from it.
Once the instance is running, you can navigate to ``http://<instance-ip>/`` and login using the following credentials:

::

    username: admin
    password: stackdio


We recommend changing this password immediately after logging in the first time.


.. _packer: https://packer.io
.. _AWS Marketplace: https://aws.amazon.com/marketplace
