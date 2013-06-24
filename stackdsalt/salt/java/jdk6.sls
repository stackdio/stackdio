jdk6_repo:
  pkgrepo:
    - managed
    - ppa: webupd8team/java

jdk6_installer_selections:
  cmd:
    - run
    - name: 'echo oracle-java6-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections'
    - unless: "debconf-get-selections | grep 'oracle-java6-installer.*shared/accepted-oracle-license-v1-1'"
    - require:
      - pkgrepo: jdk6_repo

jdk6_refresh_db:
  module:
    - run
    - name: pkg.refresh_db
    - require:
      - pkgrepo: jdk6_repo

oracle-java6-installer:
  pkg:
    - installed
    - name: oracle-java6-installer
    - require:
      - module: jdk6_refresh_db
      - file: /etc/environment

# JAVA_HOME globally
/etc/environment:
  file:
    - append
    - text: 'JAVA_HOME="{{ pillar.jdk6.java_home }}"'
    - require:
      - pkgrepo: jdk6_repo
