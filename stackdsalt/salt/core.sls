# Set the hostname of the machine based on the FQDN defined in a grain
set_hostname:
  cmd:
    - run
    - order: 1
    - name: "hostname {{ grains['fqdn'] }}"
    - unless: "hostname | grep {{ grains['fqdn'] }}"

# Make sure the FQDN for the machine is also present in loopback lookups
/etc/hosts:
  file:
    - sed
    - order: 1
    - before: '127.0.0.1 localhost'
    - after: "127.0.0.1 {{ grains['fqdn'] }} localhost"
    - limit: '^127\.0\.0\.1 '
