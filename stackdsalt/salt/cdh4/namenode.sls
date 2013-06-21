{% set mapred_local_dir='/mnt/hadoop/mapred/local' %}

# From cloudera, CDH4 requires JDK6, so include it along with the 
# CDH4 repository to install their packages.

include:
  - cdh4.repo
  - cdh4.jobtracker
  - java.jdk6

##
# Installs the namenode package and starts the service.
#
# Depends on: JDK6
##
hadoop-hdfs-namenode:
  pkg:
    - installed 
    - require:
      - pkg: oracle-java6-installer
      - module: cdh4_refresh_db
  service:
    - running
    - require: 
      - pkg: hadoop-hdfs-namenode
      - file: /etc/hadoop/conf/core-site.xml
      - file: /etc/hadoop/conf/hdfs-site.xml
      - file: /etc/hadoop/conf/mapred-site.xml
      # Make sure HDFS is initialized before the namenode
      # is started
      - cmd: init_hdfs
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
      - pkg: hadoop-hdfs-namenode

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

# Make sure the namenode metadata directory exists
# and is owned by the hdfs user
cdh4_dfs_dirs:
  cmd:
    - run
    - name: 'mkdir -p /mnt/hadoop/dfs/nn && chown -R hdfs:hdfs /mnt/hadoop'
    - unless: 'test -d /mnt/hadoop/dfs/nn'
    - require:
      - pkg: hadoop-hdfs-namenode

# Initialize HDFS. This should only run once, immediately
# following an install of hadoop.
init_hdfs:
  cmd:
    - run
    - user: hdfs
    - group: hdfs
    - name: 'hdfs namenode -format'
    - unless: 'test -d /mnt/hadoop/dfs/nn/current'
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
    - name: 'hadoop fs -mkdir -p /var/lib/hadoop-hdfs/cache/mapred/mapred/staging && hadoop fs -chmod 1777 /var/lib/hadoop-hdfs/cache/mapred/mapred/staging && hadoop fs -chown -R mapred /var/lib/hadoop-hdfs/cache/mapred'
    - unless: 'hadoop fs -test -d /var/lib/hadoop-hdfs/cache/mapred/mapred/staging'
    - require:
      - service: hadoop-hdfs-namenode
