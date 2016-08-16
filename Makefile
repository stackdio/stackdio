# Makefile for stackdio-server
#

.PHONY: all clean bower_install build_ui pep8 pylint test tar wheel

all: clean build_ui pep8 pylint test tar wheel

clean:
	rm -rf dist/ build/ *.egg-info/ htmlcov/ tests.xml stackdio/ui/static/stackdio/lib/ stackdio/ui/static/stackdio/build/

bower_install:
	bower install

build_ui: bower_install
	python manage.py build_ui

pep8:
	pep8 stackdio

pylint:
	pylint stackdio

test:
	py.test --cov=stackdio --cov-report=html --junit-xml=tests.xml stackdio

tar: build_ui
	python setup.py sdist

wheel: build_ui
	python setup.py bdist_wheel
