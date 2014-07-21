install-ntpd:
  pkg:
    - installed
    - pkgs:
      - ntp
      - ntpdate
      - ntp-doc

sync-ntpd:
  cmd.run:
    - name: 'ntpdate 0.centos.pool.ntp.org'
    - unless: 'service ntpd status'
    - require:
      - pkg: install-ntpd

start-ntpd:
  service:
    - running
    - name: ntpd
    - enable: true
    - require:
      - cmd: sync-ntpd
