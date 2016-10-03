#!/usr/bin/env bash

mkdir mkdir ${HOME}/.stackdio

# We only care about these 2 envs

if [ "$DB" == "postgres" ]; then
    cp ${TRAVIS_BUILD_DIR}/tests/stackdio-travis-postgres.yaml ${HOME}/.stackdio/stackdio.yaml
fi

if [ "$DB" == "mysql" ]; then
    cp ${TRAVIS_BUILD_DIR}/tests/stackdio-travis-mysql.yaml ${HOME}/.stackdio/stackdio.yaml
fi
