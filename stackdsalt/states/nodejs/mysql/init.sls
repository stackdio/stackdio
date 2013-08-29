mysql-server:
  pkg:
    - installed

mysql:
  service:
    - running
    - require:
      - pkg: mysql-server
