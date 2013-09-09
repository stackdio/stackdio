{% set extjs_zip = 'ext-2.2.zip' %}
{% set oozie_data_dir = '/var/lib/oozie' %}
include:
  - cdh4.repo

unzip:
  pkg:
    - installed

oozie:
  pkg:
    - installed
    - pkgs:
      - oozie
      - oozie-client
    - require:
      - module: cdh4_refresh_db
  service:
    - running
    - require:
      - cmd: extjs
      - cmd: ooziedb

extjs:
  file:
    - managed
    - name: /srv/sync/cdh4/{{ extjs_zip }}
    - source: salt://cdh4/files/{{ extjs_zip }}
    - user: root
    - group: root
    - mode: 644
    - require:
      - pkg: oozie
  cmd:
    - run
    - name: 'unzip -d {{ oozie_data_dir }} /srv/sync/cdh4/{{ extjs_zip }} &> /dev/null'
    - unless: 'test -d {{ oozie_data_dir }}/ext-*'
    - require:
      - file: /srv/sync/cdh4/{{ extjs_zip }}
      - pkg: unzip
      - pkg.installed: oozie

ooziedb:
  cmd:
    - run
    - name: '/usr/lib/oozie/bin/ooziedb.sh create -run'
    - unless: 'test -d {{ oozie_data_dir }}/oozie-db'
    - require:
      - pkg.installed: oozie
