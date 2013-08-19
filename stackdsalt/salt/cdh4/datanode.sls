{% set mapred_local_dir = salt['pillar.get']('cdh4:mapred:local_dir') %}
{% set dfs_data_dir = salt['pillar.get']('cdh4:dfs:data_dir') %}

# From cloudera, CDH4 requires JDK6, so include it along with the 
# CDH4 repository to install their packages.
include:
  - cdh4.repo
  - java.jdk6

##
# Installs the datanode service
#
# Depends on: JDK6
#
##
hadoop-hdfs-datanode:
  pkg:
    - installed 
    - version: 4.2.1
    - require:
      - pkg: oracle-java6-installer
      - module: cdh4_refresh_db
  service:
    - running
    - require: 
      - pkg: hadoop-hdfs-datanode
      - cmd: dfs_data_dir
      - file: /etc/hadoop/conf/core-site.xml
      - file: /etc/hadoop/conf/hdfs-site.xml
      - file: /etc/hadoop/conf/mapred-site.xml
      - file: /etc/hadoop/conf/hadoop-env.sh
    - watch:
      - file: /etc/hadoop/conf/core-site.xml
      - file: /etc/hadoop/conf/hdfs-site.xml
      - file: /etc/hadoop/conf/mapred-site.xml
      - file: /etc/hadoop/conf/hadoop-env.sh

##
# Installs the task tracker service
#
# Depends on: JDK6
##
hadoop-0.20-mapreduce-tasktracker:
  pkg:
    - installed 
    - version: 4.2.1
    - require:
      - pkg: oracle-java6-installer
      - module: cdh4_refresh_db
  service:
    - running
    - require: 
      - pkg: hadoop-0.20-mapreduce-tasktracker
      - cmd: mapred_local_dirs
      - file: /etc/hadoop/conf/core-site.xml
      - file: /etc/hadoop/conf/hdfs-site.xml
      - file: /etc/hadoop/conf/mapred-site.xml
      - file: /etc/hadoop/conf/hadoop-env.sh
    - watch:
      - file: /etc/hadoop/conf/core-site.xml
      - file: /etc/hadoop/conf/hdfs-site.xml
      - file: /etc/hadoop/conf/mapred-site.xml
      - file: /etc/hadoop/conf/hadoop-env.sh

# Set up hadoop environment. This file is loaded automatically
# by most of the hadoop services when needed
/etc/hadoop/conf/hadoop-env.sh:
  file:
    - managed
    - source: salt://cdh4/etc/hadoop/conf/hadoop-env.sh
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - require:
      - pkg: hadoop-hdfs-datanode
      - pkg: hadoop-0.20-mapreduce-tasktracker

# Render the configuration files and put them
# in the right locations
/etc/hadoop/conf/mapred-site.xml:
  file:
    - managed
    - source: salt://cdh4/etc/hadoop/conf/mapred-site.xml
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - require:
      - pkg: hadoop-hdfs-datanode
      - pkg: hadoop-0.20-mapreduce-tasktracker

/etc/hadoop/conf/core-site.xml:
  file:
    - managed
    - source: salt://cdh4/etc/hadoop/conf/core-site.xml
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - require:
      - pkg: hadoop-hdfs-datanode
      - pkg: hadoop-0.20-mapreduce-tasktracker

/etc/hadoop/conf/hdfs-site.xml:
  file:
    - managed
    - source: salt://cdh4/etc/hadoop/conf/hdfs-site.xml
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - require:
      - pkg: hadoop-hdfs-datanode
      - pkg: hadoop-0.20-mapreduce-tasktracker

# make the local storage directories
mapred_local_dirs:
  cmd:
    - run
    - name: 'mkdir -p {{ mapred_local_dir }} && chmod -R 755 {{ mapred_local_dir }} && chown -R mapred:mapred {{ mapred_local_dir }}'
    - unless: "test -d {{ mapred_local_dir }} && [ `stat -c '%U' {{ mapred_local_dir }}` == 'mapred' ]"
    - require:
      - pkg: hadoop-0.20-mapreduce-tasktracker

# make the hdfs data directories
dfs_data_dir:
  cmd:
    - run
    - name: 'mkdir -p {{ dfs_data_dir }} && chmod -R 755 {{ dfs_data_dir }} && chown -R hdfs:hdfs {{ dfs_data_dir }}'
    - unless: "test -d {{ dfs_data_dir }} && [ `stat -c '%U' {{ dfs_data_dir }}` == 'hdfs' ]"
    - require:
      - pkg: hadoop-hdfs-datanode
