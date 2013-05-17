#!/bin/bash

USER=$MYSQL_USER
PASS=$MYSQL_PASS

if [ "$1" != "--force" ]; then
    echo "Sorry, you must use the force luke!"
    exit 1
fi

DB_NAME=$2
if [ -z "$DB_NAME" ]; then
    echo "Must provide the database name"
    exit 1 
fi

echo "Dropping database $DB_NAME..."
mysqladmin -u$MYSQL_USER -p$MYSQL_PASS drop $DB_NAME && mysqladmin -u$MYSQL_USER -p$MYSQL_PASS create $DB_NAME
