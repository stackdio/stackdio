Using the Amazon AMI
====================

To make installation easier, we provide an `packer`_ build that creates an Amazon Machine Image (AMI).
This AMI is built from an Ubuntu 14.04 LTS image, and is HVM based.  While our ultimate plan is to
provide this AMI on the `AWS Marketplace`_, we don't have this set up yet.


Building an AMI
---------------

If you haven't already, install packer using their documentation `here <https://packer.io/docs/installation.html>`_.
We recommend using homebrew for the installation if you're using OSX.

You must also have `npm`_ and `bower`_ installed locally before you can build the AMI.
``npm`` can almost always be installed with your favorite package manager, and ``bower`` is
installed with the following command (after you install ``npm``):

.. code:: bash

    npm install -g bower


First you must clone the github repository:

.. code:: bash

    git clone https://github.com/stackdio/stackdio.git
    cd stackdio

Then, run the packer build:

.. code:: bash

    ./packer/build.sh


After a few minutes, you should have a usable AMI.


Using the AMI
-------------

After you've built the AMI, you can launch an instance from it.  Once the instance is running,
you can navigate to ``http://<instance-ip>/`` and login using the following credentials:

::

    username: admin
    password: stackdio


We recommend changing this password immediately after logging in the first time.


.. _packer: https://packer.io
.. _AWS Marketplace: https://aws.amazon.com/marketplace
.. _npm: https://www.npmjs.com
.. _bower: http://bower.io