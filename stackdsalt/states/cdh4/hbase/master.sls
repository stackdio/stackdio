{% set hbase_tmp_dir = salt['pillar.get']('cdh4:hbase:tmp_dir') %}
{% set zk_data_dir = salt['pillar.get']('cdh4:zookeeper:data_dir') %}

include:
  - cdh4.repo
  - cdh4.hadoop.client
  - cdh4.hbase.regionserver_hostnames
  - cdh4.zookeeper
  - cdh4.hbase.conf
  - cdh4.landing_page

hbase-init:
  cmd:
    - run
    - user: hdfs
    - group: hdfs
    - name: 'hadoop fs -mkdir /hbase && hadoop fs -chown hbase:hbase /hbase'
    - unless: 'hadoop fs -test -d /hbase'
    - require:
      - pkg: hadoop-client

hbase-master:
  pkg:
    - installed 
    - require:
      - cmd: hbase-init
      - service.running: zookeeper-start
      - service.running: zookeeper-server
      - file: append_regionservers_etc_hosts
  service:
    - running
    - require: 
      - pkg: hbase-master
      - file: /etc/hbase/conf/hbase-site.xml
    - watch:
      - file: /etc/hbase/conf/hbase-site.xml
