#!/bin/bash

export STACKDIO_VERSION=`python setup.py --version`

bower install
python setup.py sdist

packer build packer/production.json
