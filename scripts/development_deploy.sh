#!/bin/bash


rsync -av ../../ --exclude='.git' --exclude='.idea' --exclude='*.pyc' --exclude='*.pyo' stackd.dev:/mnt/clark