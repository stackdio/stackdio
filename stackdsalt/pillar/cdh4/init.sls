cdh4:
  version: 4.2.1
  io:
    sort_factor: 25
    sort_mb: 250
  dfs:
    name_dir: /mnt/hadoop/hdfs/nn
    data_dir: /mnt/hadoop/hdfs/data
    permissions: true
  mapred:
    local_dir: /mnt/hadoop/mapred/local
    system_dir: /hadoop/system/mapred
    reduce_tasks: {{ 3 * (grains['cluster_size']-1) }}
    map_tasks_max: 5
    reduce_tasks_max: 3
    child_java_opts: '-Xmx2000m'
    child_ulimit: 8000000
  hbase:
    tmp_dir: /mnt/hbase/tmp
    replication: 3
  zookeeper:
    data_dir: /mnt/zk/data
