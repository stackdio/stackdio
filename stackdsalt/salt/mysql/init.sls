mysql-server:
  pkg:
    - installed

mysql:
  service:
    - running
    - require:
      - file: /etc/mysql/my.cnf
      - pkg: mysql-server
    - watch:
      - file: /etc/mysql/my.cnf

/etc/mysql/my.cnf:
  file.sed:
    - before: '^bind-address.*127\.0\.0\.1$'
    - after: 'bind-address = 0.0.0.0'
    - require:
      - pkg: mysql-server
