# Set the hostname of the machine based on the FQDN defined in a grain
set_hostname:
  cmd:
    - run
    - order: 1
    - name: "hostname {{ grains['fqdn'] }}"
    - unless: "hostname | grep {{ grains['fqdn'] }}"

# Add a mapping to FQDN from local IP address
append_fqdn_etc_hosts:
  file:
    - append
    - order: 1
    - name: /etc/hosts
    - text: "{{ grains['ip_interfaces']['eth0'][0] }} {{ grains['fqdn'] }}"
  require:
    - cmd: set_hostname

{% if grains['os_family'] == 'Debian' %}
/etc/hostname:
  file:
    - sed
    - order: 1
    - before: "^.*$"
    - after: "{{ grains['fqdn'] }}"
    - require:
      - cmd: set_hostname
{% elif grains['os_family'] == 'RedHat' %}
/etc/sysconfig/network:
  file:
    - sed
    - order: 1
    - before: "^HOSTNAME=.*$"
    - after: "HOSTNAME={{ grains['fqdn'] }}"
    - require:
      - cmd: set_hostname
{% endif %}
