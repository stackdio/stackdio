{% if grains['os_family'] == 'Debian' %}
    {% set ntp_name = 'ntp' %}
{% else %}
    {% set ntp_name = 'ntpd' %}
{% endif %}

install-ntpd:
  pkg:
    - installed
    - pkgs:
      - ntp
      - ntpdate
      - ntp-doc

sync-ntpd:
  cmd.run:
    - name: 'ntpdate 0.centos.pool.ntp.org 1.centos.pool.ntp.org 2.centos.pool.ntp.org 3.centos.pool.ntp.org'
    - unless: 'service {{ ntp_name }} status'
    - require:
      - pkg: install-ntpd

start-ntpd:
  service:
    - running
    - name: {{ ntp_name }}
    - enable: true
    - require:
      - cmd: sync-ntpd
