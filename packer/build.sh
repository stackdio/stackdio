#!/bin/bash

# Grab the base dir
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DIR="$( cd "$( dirname "${DIR}" )" && pwd )"

cd ${DIR}

# install bower dependencies
bower install

# Build the UI
python manage.py build_ui

# Grab the version
export STACKDIO_VERSION=`python setup.py --version`

# Create our artifact
python setup.py bdist_wheel

# Run the build
packer build packer/build.json
