{% set ntp_name = salt['grains.filter_by']({
  'Debian': 'ntp',
  'RedHat': 'ntpd',
}, default='Debian') %}

install-ntpd:
  pkg.installed:
    - pkgs:
      - ntp
      - ntpdate

start-ntpd:
  service.running:
    - name: {{ ntp_name }}
    - enable: true
    - require:
      - pkg: install-ntpd
