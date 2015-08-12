{% if grains['os_family'] == 'Debian' %}
    {% set hostname_service = 'hostname' %}
{% elif grains['os_family'] == 'RedHat' %}
    {% set hostname_service = 'network' %}
{% endif %}


# Edit the appropriate hostname file
{% if grains['os_family'] == 'Debian' %}
hostname_file:
  file:
    - sed
    - user: root
    - name: /etc/hostname
    - order: 1
    - before: "^.*$"
    - after: "{{ grains['fqdn'] }}"
{% elif grains['os_family'] == 'RedHat' %}
hostname_file:
  file:
    - sed
    - user: root
    - name: /etc/sysconfig/network
    - order: 1
    - before: "^HOSTNAME=.*$"
    - after: "HOSTNAME={{ grains['fqdn'] }}"
{% endif %}

# Add an IP->FQDN mapping for each machine in the stack
stack_hostnames:
  file:
    - managed
    - user: root
    - group: root
    - mode: 644
    - name: /etc/hosts
    - template: jinja
    - source: salt://core/etc/hosts
    - require:
      - file: hostname_file

# Set the hostname of the machine based on the FQDN defined in a grain
set_hostname:
  cmd:
    - run
    - order: 1
    - user: root
    - name: "hostname {{ grains['fqdn'] }}"
    - unless: "hostname | grep {{ grains['fqdn'] }}"
    - require:
      - file: stack_hostnames

# Restart the apropriate service for this change to take effect
restart_hostname:
  cmd:
    - run
    - user: root
    - name: "service {{ hostname_service }} restart"
    - require:
      - cmd: set_hostname
