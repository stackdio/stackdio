{% set mapred_local_dir = salt['pillar.get']('cdh4:mapred:local_dir') %}
{% set dfs_data_dir = salt['pillar.get']('cdh4:dfs:data_dir') %}

# From cloudera, CDH4 requires JDK6, so include it along with the 
# CDH4 repository to install their packages.
include:
  - cdh4.repo
  - cdh4.hadoop.conf
  - cdh4.landing_page

##
# Installs the datanode service
#
# Depends on: JDK6
#
##
hadoop-hdfs-datanode:
  pkg:
    - installed 
    - require:
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
    - require:
      - module: cdh4_refresh_db
  service:
    - running
    - require: 
      - pkg: hadoop-0.20-mapreduce-tasktracker
      - cmd: datanode_mapred_local_dirs
      - file: /etc/hadoop/conf/core-site.xml
      - file: /etc/hadoop/conf/hdfs-site.xml
      - file: /etc/hadoop/conf/mapred-site.xml
      - file: /etc/hadoop/conf/hadoop-env.sh
    - watch:
      - file: /etc/hadoop/conf/core-site.xml
      - file: /etc/hadoop/conf/hdfs-site.xml
      - file: /etc/hadoop/conf/mapred-site.xml
      - file: /etc/hadoop/conf/hadoop-env.sh

# make the local storage directories
datanode_mapred_local_dirs:
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
