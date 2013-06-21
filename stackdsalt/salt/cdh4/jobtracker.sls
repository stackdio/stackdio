# From cloudera, CDH4 requires JDK6, so include it along with the 
# CDH4 repository to install their packages.
include:
  - cdh4.repo
  - java.jdk6

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
      - pkg: hadoop-hdfs-namenode
  service:
    - running
    - require: 
      - pkg: hadoop-0.20-mapreduce-jobtracker
      - pkg: hadoop-hdfs-namenode
      - cmd: mapred_system_dir
    - watch:
      - file: /etc/hadoop/conf/core-site.xml
      - file: /etc/hadoop/conf/hdfs-site.xml
      - file: /etc/hadoop/conf/mapred-site.xml

mapred_system_dir:
  cmd:
    - run
    - user: hdfs
    - group: hdfs
    - name: 'hadoop fs -mkdir /hadoop/system/mapred && hadoop fs -chown mapred:hadoop /hadoop/system/mapred'
    - unless: 'hadoop fs -test -d /hadoop/system/mapred'
    - require:
      - service: hadoop-hdfs-namenode
