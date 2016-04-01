{% if grains['os_family'] == 'Debian' %}
    {% set ntp_name = 'ntp' %}
{% else %}
    {% set ntp_name = 'ntpd' %}

# CentOS apparently needs yum-utils for pkg.installed to work, but we can't install it with pkg.installed
install-yum-utils:
  cmd:
    - run
    - name: 'yum install -y yum-utils'
    - user: root
    - require_in:
      - pkg: install-ntpd

{% endif %}

install-ntpd:
  pkg:
    - installed
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
  service:
    - running
    - name: {{ ntp_name }}
    - enable: true
    - require:
      - cmd: sync-ntpd
