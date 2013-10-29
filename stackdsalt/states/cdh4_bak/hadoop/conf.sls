{% set datanode = 'cdh4.hadoop.datanode' in grains.get('roles', []) %}
{% set namenode = 'cdh4.hadoop.namenode' in grains.get('roles', []) %}

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
{% if datanode %}
      - pkg: hadoop-hdfs-datanode
      - pkg: hadoop-0.20-mapreduce-tasktracker
{% endif %}
{% if namenode %}
      - pkg: hadoop-hdfs-namenode
      - pkg: hadoop-0.20-mapreduce-jobtracker
{% endif %}

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
{% if datanode %}
      - pkg: hadoop-hdfs-datanode
      - pkg: hadoop-0.20-mapreduce-tasktracker
{% endif %}
{% if namenode %}
      - pkg: hadoop-hdfs-namenode
      - pkg: hadoop-0.20-mapreduce-jobtracker
{% endif %}

/etc/hadoop/conf/core-site.xml:
  file:
    - managed
    - source: salt://cdh4/etc/hadoop/conf/core-site.xml
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - require:
{% if datanode %}
      - pkg: hadoop-hdfs-datanode
      - pkg: hadoop-0.20-mapreduce-tasktracker
{% endif %}
{% if namenode %}
      - pkg: hadoop-hdfs-namenode
      - pkg: hadoop-0.20-mapreduce-jobtracker
{% endif %}

/etc/hadoop/conf/hdfs-site.xml:
  file:
    - managed
    - source: salt://cdh4/etc/hadoop/conf/hdfs-site.xml
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - require:
{% if datanode %}
      - pkg: hadoop-hdfs-datanode
      - pkg: hadoop-0.20-mapreduce-tasktracker
{% endif %}
{% if namenode %}
      - pkg: hadoop-hdfs-namenode
      - pkg: hadoop-0.20-mapreduce-jobtracker
{% endif %}
