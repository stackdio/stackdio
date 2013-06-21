include:
  - cdh4.repo

hadoop-client: 
  pkg:
    - installed
    - require:
      - file: /etc/apt/sources.list.d/cloudera.list
