{% set master = 'cdh4.hbase.master' in grains.get('roles', []) %}
{% set regionserver = 'cdh4.master.regionserver' in grains.get('roles', []) %}


/etc/hbase/conf/hbase-site.xml:
  file:
    - managed
    - source: salt://cdh4/etc/hbase/conf/hbase-site.xml
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - require:
{% if regionserver %}
      - pkg: hbase-regionserver
{% endif %}
{% if master %}
      - pkg: hbase-master
{% endif %}
