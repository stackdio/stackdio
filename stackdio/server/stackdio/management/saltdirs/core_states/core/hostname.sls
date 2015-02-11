{% if grains['os_family'] == 'Debian' %}
    {% set hostname_service = 'hostname' %}
{% elif grains['os_family'] == 'RedHat' %}
    {% set hostname_service = 'network' %}
{% endif %}

{%- set stack_hosts = salt['mine.get']('stack_id:' ~ grains.stack_id, 'grains.items', 'grain') -%}


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
    - append
    - user: root
    - name: /etc/hosts
    - text:
{%- for host, items in stack_hosts.iteritems() %}
      - "{{ items['ip_interfaces']['eth0'][0] }} {{ items['fqdn'] }} {{ items['id'] }}"
{% endfor %}
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
