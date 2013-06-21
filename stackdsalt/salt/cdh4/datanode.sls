{% set mapred_local_dir='/mnt/hadoop/mapred/local' %}
{% set mapred_data_dir='/mnt/hadoop/hdfs/data' %}

# From cloudera, CDH4 requires JDK6, so include it along with the 
# CDH4 repository to install their packages.
include:
  - cdh4.repo
  - java.jdk6

##
# Installs the task tracker service
#
# Depends on: JDK6
##
hadoop-0.20-mapreduce-tasktracker:
  pkg:
    - installed 
    - require:
      - pkg: oracle-java6-installer
      - module: cdh4_refresh_db
  service:
    - running
    - require: 
      - pkg: hadoop-0.20-mapreduce-tasktracker
      - file: /etc/hadoop/conf/core-site.xml
      - file: /etc/hadoop/conf/hdfs-site.xml
      - file: /etc/hadoop/conf/mapred-site.xml
    - watch:
      - file: /etc/hadoop/conf/core-site.xml
      - file: /etc/hadoop/conf/hdfs-site.xml
      - file: /etc/hadoop/conf/mapred-site.xml

##
# Installs the datanode service
#
# Depends on: JDK6
##
hadoop-hdfs-datanode:
  pkg:
    - installed 
    - require:
      - pkg: oracle-java6-installer
      - module: cdh4_refresh_db
  service:
    - running
    - require: 
      - pkg: hadoop-hdfs-datanode
      - file: /etc/hadoop/conf/core-site.xml
      - file: /etc/hadoop/conf/hdfs-site.xml
      - file: /etc/hadoop/conf/mapred-site.xml
    - watch:
      - file: /etc/hadoop/conf/core-site.xml
      - file: /etc/hadoop/conf/hdfs-site.xml
      - file: /etc/hadoop/conf/mapred-site.xml

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
    - defaults:
       # TODO: Move this to pillar data
       io_sort_factor: 25
       io_sort_mb: 250
       mapred_local_dir: {{ mapred_local_dir }}
       mapred_reduce_tasks: {{ 3 * (grains['cluster_size']-1) }}
       mapred_map_tasks_max: 5
       mapred_reduce_tasks_max: 3
       mapred_child_java_opts: '-Xmx2000m'
       mapred_child_ulimit: 8000000
    - require:
      - pkg: hadoop-0.20-mapreduce-tasktracker
      - pkg: hadoop-hdfs-datanode

/etc/hadoop/conf/core-site.xml:
  file:
    - managed
    - source: salt://cdh4/etc/hadoop/conf/core-site.xml
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - require:
      - pkg: hadoop-0.20-mapreduce-tasktracker
      - pkg: hadoop-hdfs-datanode

/etc/hadoop/conf/hdfs-site.xml:
  file:
    - managed
    - source: salt://cdh4/etc/hadoop/conf/hdfs-site.xml
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - require:
      - pkg: hadoop-0.20-mapreduce-tasktracker
      - pkg: hadoop-hdfs-datanode

# make the local storage directories
mapred_local_dirs:
  cmd:
    - run
    - name: 'mkdir -p {{ mapred_local_dir}} && chmod -R 755 {{ mapred_local_dir }} && chown -R mapred:hadoop {{ mapred_local_dir }}'
    - unless: 'test -d {{ mapred_local_dir }}'
    - require:
      - pkg: hadoop-hdfs-datanode

# make the hdfs data directories
hdfs_data_dir:
  cmd:
    - run
    - name: 'mkdir -p {{ mapred_data_dir}} && chmod -R 755 {{ mapred_data_dir }} && chown -R mapred:hadoop {{ mapred_data_dir }}'
    - unless: 'test -d {{ mapred_data_dir }}'
    - require:
      - pkg: hadoop-hdfs-datanode
