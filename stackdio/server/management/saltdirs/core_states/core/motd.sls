/etc/motd:
   file.managed:
     - template: jinja
     - user: root
     - group: root
     - mode: 444
     - source: salt://core/motd.jinja2
