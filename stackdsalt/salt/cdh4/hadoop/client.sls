include:
  - cdh4.repo

hadoop-client: 
  pkg:
    - installed
    - require:
      - module: cdh4_refresh_db
