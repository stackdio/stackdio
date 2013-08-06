# Set the hostname of the machine based on the FQDN defined in a grain
set_hostname:
  cmd:
    - run
    - order: 1
    - name: "hostname {{ grains['fqdn'] }}"
    - unless: "hostname | grep {{ grains['fqdn'] }}"

# clean out old entries
cleanup_etc_hosts:
  file:
    - sed
    - order: 1
    - name: /etc/hosts
    - before: "^.* {{ grains['fqdn'] }}$"
    - after: ''
    - require:
      - cmd: set_hostname

# Add a mapping to FQDN from local IP address
/etc/hosts:
  file:
    - append
    - order: 1
    - text: "{{ grains['ip_interfaces']['eth0'][0] }} {{ grains['fqdn'] }}"
    - require:
      - file: cleanup_etc_hosts
