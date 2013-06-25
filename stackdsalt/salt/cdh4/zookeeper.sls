# TODO: Need to handle the case where the
# zookeeper is not on the namenode
zookeeper-server:
  pkg:
    - installed
  service:
    - running
    - require:
      - pkg: zookeeper-server

zookeeper-init:
  cmd:
    - run
    - name: 'service zookeeper-server init'
    - unless: 'ls /var/lib/zookeeper/*'
    - require:
      - pkg: zookeeper-server