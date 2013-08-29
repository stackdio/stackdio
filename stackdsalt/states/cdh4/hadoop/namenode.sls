{% set dfs_name_dir = salt['pillar.get']('cdh4:dfs:name_dir') %}
{% set mapred_local_dir = salt['pillar.get']('cdh4:mapred:local_dir') %}
{% set mapred_system_dir = salt['pillar.get']('cdh4:mapred:system_dir') %}
{% set mapred_staging_dir = '/var/lib/hadoop-hdfs/cache/mapred/mapred/staging' %}

# From cloudera, CDH4 requires JDK6, so include it along with the 
# CDH4 repository to install their packages.

include:
  - cdh4.repo

##
# Installs the namenode package and starts the service.
#
# Depends on: JDK6
##
hadoop-hdfs-namenode:
  pkg:
    - installed 
    - require:
      - module: cdh4_refresh_db
  service:
    - running
    - require: 
      - pkg: hadoop-hdfs-namenode
      # Make sure HDFS is initialized before the namenode
      # is started
      - cmd: init_hdfs
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
# Installs the hadoop job tracker service and starts it.
#
# Depends on: JDK6
##
hadoop-0.20-mapreduce-jobtracker:
  pkg:
    - installed
    - require:
      - module: cdh4_refresh_db
  service:
    - running
    - require: 
      - pkg: hadoop-0.20-mapreduce-jobtracker
      - cmd: mapred_local_dirs
      - cmd: mapred_system_dirs
      - cmd: hdfs_mapreduce_var_dir
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
      - pkg: hadoop-hdfs-namenode
      - pkg: hadoop-0.20-mapreduce-jobtracker

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
      - pkg: hadoop-hdfs-namenode
      - pkg: hadoop-0.20-mapreduce-jobtracker

/etc/hadoop/conf/core-site.xml:
  file:
    - managed
    - source: salt://cdh4/etc/hadoop/conf/core-site.xml
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - require:
      - pkg: hadoop-hdfs-namenode
      - pkg: hadoop-0.20-mapreduce-jobtracker

/etc/hadoop/conf/hdfs-site.xml:
  file:
    - managed
    - source: salt://cdh4/etc/hadoop/conf/hdfs-site.xml
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - require:
      - pkg: hadoop-hdfs-namenode
      - pkg: hadoop-0.20-mapreduce-jobtracker

# Make sure the namenode metadata directory exists
# and is owned by the hdfs user
cdh4_dfs_dirs:
  cmd:
    - run
    - name: 'mkdir -p {{ dfs_name_dir }} && chown -R hdfs:hdfs `dirname {{ dfs_name_dir }}`'
    - unless: 'test -d {{ dfs_name_dir }}'
    - require:
      - pkg: hadoop-hdfs-namenode
      - file: /etc/hadoop/conf/core-site.xml
      - file: /etc/hadoop/conf/hdfs-site.xml
      - file: /etc/hadoop/conf/mapred-site.xml
      - file: /etc/hadoop/conf/hadoop-env.sh

# Initialize HDFS. This should only run once, immediately
# following an install of hadoop.
init_hdfs:
  cmd:
    - run
    - user: hdfs
    - group: hdfs
    - name: 'hdfs namenode -format'
    - unless: 'test -d {{ dfs_name_dir }}/current'
    - require:
      - cmd: cdh4_dfs_dirs

# HDFS tmp directory
hdfs_tmp_dir:
  cmd:
    - run
    - user: hdfs
    - group: hdfs
    - name: 'hadoop fs -mkdir /tmp && hadoop fs -chmod -R 1777 /tmp'
    - unless: 'hadoop fs -test -d /tmp'
    - require:
      - service: hadoop-hdfs-namenode

# HDFS MapReduce var directories
hdfs_mapreduce_var_dir:
  cmd:
    - run
    - user: hdfs
    - group: hdfs
    - name: 'hadoop fs -mkdir -p {{ mapred_staging_dir }} && hadoop fs -chmod 1777 {{ mapred_staging_dir }} && hadoop fs -chown -R mapred `dirname {{ mapred_staging_dir }}`'
    - unless: 'hadoop fs -test -d {{ mapred_staging_dir }}'
    - require:
      - service: hadoop-hdfs-namenode

# MR local directory
mapred_local_dirs:
  cmd:
    - run
    - name: 'mkdir -p {{ mapred_local_dir }} && chown -R mapred:hadoop {{ mapred_local_dir }}'
    - unless: 'test -d {{ mapred_local_dir }}'
    - require:
      - pkg: hadoop-hdfs-namenode
      - pkg: hadoop-0.20-mapreduce-jobtracker

# MR system directory
mapred_system_dirs:
  cmd:
    - run
    - user: hdfs
    - group: hdfs
    - name: 'hadoop fs -mkdir {{ mapred_system_dir }} && hadoop fs -chown mapred:hadoop {{ mapred_system_dir }}'
    - unless: 'hadoop fs -test -d {{ mapred_system_dir }}'
    - require:
      - service: hadoop-hdfs-namenode
