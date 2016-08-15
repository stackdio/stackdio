# Makefile for stackdio-server
#

.PHONY: clean test tar wheel pep8 pylint

test:
	py.test --cov=stackdio --cov-report=html --junit-xml=tests.xml stackdio

pep8:
	pep8 stackdio

pylint:
	pylint stackdio

bower_install:
	bower install

build_ui: bower_install
	python manage.py build_ui

tar: build_ui
	python setup.py sdist

wheel: build_ui
	python setup.py bdist_wheel

clean:
	rm -rf dist/ build/ *.egg-info/ .coverage htmlcov/ tests.xml stackdio/ui/static/stackdio/lib/ stackdio/ui/static/stackdio/build/
