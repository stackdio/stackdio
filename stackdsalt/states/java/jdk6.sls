# Debian OS family only...I couldn't find a yum repository that had
# java6, so for now we're requiring the OS to already have it installed

{% if grains['os_family'] == 'Debian' %}
# add the oracle apt repository
jdk6_repo:
  pkgrepo:
    - managed
    - ppa: webupd8team/java

# accept the license agreement for a headless install
jdk6_installer_selections:
  cmd:
    - run
    - name: 'echo oracle-java6-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections'
    - require:
      - pkgrepo: jdk6_repo

# ie, apt-get update
jdk6_refresh_db:
  module:
    - run
    - name: pkg.refresh_db
    - require:
      - pkgrepo: jdk6_repo

# JAVA_HOME globally
/etc/environment:
  file:
    - append
    - text: 'JAVA_HOME="{{ pillar.jdk6.java_home }}"'
    - require:
      - pkgrepo: jdk6_repo

# install java6
oracle-java6-installer:
  pkg:
    - installed
    - name: oracle-java6-installer
    - require:
      - cmd: jdk6_installer_selections
      - module: jdk6_refresh_db
      - file: /etc/environment
{% endif %}
