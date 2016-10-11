{% if grains['os_family'] == 'Debian' %}
    {% set hostname_service = 'hostname' %}
{% elif grains['os_family'] == 'RedHat' %}
    {% set hostname_service = 'network' %}
{% endif %}


# Edit the appropriate hostname file
hostname_file:
  file.replace:
{% if grains['os_family'] == 'Debian' %}
    - name: /etc/hostname
    - pattern: "^.*$"
    - repl: "{{ grains['fqdn'] }}"
{% elif grains['os_family'] == 'RedHat' %}
    - name: /etc/sysconfig/network
    - pattern: "^HOSTNAME=.*$"
    - repl: "HOSTNAME={{ grains['fqdn'] }}"
{% endif %}

# Add an IP->FQDN mapping for each machine in the stack
stack_hostnames:
  file.managed:
    - user: root
    - group: root
    - mode: 644
    - name: /etc/hosts
    - template: jinja
    - source: salt://core/etc/hosts

# Set the hostname of the machine based on the FQDN defined in a grain
set_hostname:
  cmd.run:
    - user: root
    - name: "hostname {{ grains['fqdn'] }}"
    - unless: "hostname | grep {{ grains['fqdn'] }}"
    - require:
      - file: hostname_file

# Restart the apropriate service for this change to take effect
hostname-svc:
  service.running:
    - name: {{ hostname_service }}
    - watch:
      - cmd: set_hostname
      - file: stack_hostnames
      - file: hostname_file
