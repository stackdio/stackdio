include:
  - cdh4.repo

hadoop-client: 
  pkg:
    - installed
    - version: 4.2.1
    - require:
      - file: /etc/apt/sources.list.d/cloudera.list
      - module: cdh4_refresh_db
