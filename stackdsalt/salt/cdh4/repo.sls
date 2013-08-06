{% if grains['os'] == 'Ubuntu' %}
# Add the appropriate CDH4 repository. See http://archive.cloudera.com/cdh4
# for which distributions and versions are supported.
/etc/apt/sources.list.d/cloudera.list:
  file:
    - managed
    - name: /etc/apt/sources.list.d/cloudera.list
    - source: salt://cdh4/etc/apt/sources.list.d/cloudera.list.template
    - user: root
    - group: root
    - mode: 644
    - template: jinja

cdh4_gpg:
  cmd:
    - run
    - name: 'curl -s http://archive.cloudera.com/cdh4/ubuntu/{{ grains["lsb_distrib_codename"] }}/amd64/cdh/archive.key | sudo apt-key add -'
    - unless: 'apt-key list | grep "Cloudera Apt Repository"'
    - require:
      - file: /etc/apt/sources.list.d/cloudera.list

cdh4_refresh_db:
  module:
    - run
    - name: pkg.refresh_db
    - require:
      - cmd: cdh4_gpg
{% endif %}
