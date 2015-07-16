/etc/init/salt-minion.conf:
  file:
    - managed
    - source: salt://core/etc/init/salt-minion.conf
