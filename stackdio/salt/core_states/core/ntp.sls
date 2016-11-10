{% if grains['os_family'] == 'Debian' %}
    {% set ntp_name = 'ntp' %}
{% else %}
    {% set ntp_name = 'ntpd' %}
{% endif %}

install-ntpd:
  pkg.installed:
    - pkgs:
      - ntp
      - ntpdate

sync-ntpd:
  cmd.run:
    - name: 'ntpdate 0.pool.ntp.org 1.pool.ntp.org 2.pool.ntp.org 3.pool.ntp.org'
    - unless: 'service {{ ntp_name }} status'
    - require:
      - pkg: install-ntpd

start-ntpd:
  service.running:
    - name: {{ ntp_name }}
    - enable: true
    - require:
      - cmd: sync-ntpd
