include:
  - cdh4.repo
  - cdh4.hbase.conf
  - cdh4.landing_page

hbase-regionserver:
  pkg:
    - installed 
    - require:
      - module: cdh4_refresh_db
  service:
    - running
    - require: 
      - pkg: hbase-regionserver
      - file: /etc/hbase/conf/hbase-site.xml
    - watch:
      - file: /etc/hbase/conf/hbase-site.xml
