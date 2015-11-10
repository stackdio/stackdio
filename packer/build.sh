#!/bin/bash

export STACKDIO_VERSION=`python setup.py --version`

python setup.py bdist_wheel

packer build packer/build.json
