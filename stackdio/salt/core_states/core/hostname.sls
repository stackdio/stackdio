{% set hostname_service = grains['filter_by']({
    'Debian': grains['filter_by']({
      '12': 'hostname',
      '14': 'hostname',
      '16': 'networking',
    }, 'osmajorrelease'),
    'RedHat': 'network',
}) %}

# Edit the appropriate hostname file
hostname_file:
  file.managed:
    {% if grains['os_family'] == 'RedHat' %}
    - name: /etc/sysconfig/network
    - contents:
      - "NOZEROCONF=yes"
      - "NETWORKING=yes"
      - "HOSTNAME={{ grains['fqdn'] }}"
    {% else %}
    - name: /etc/hostname
    - contents:
      - "{{ grains['fqdn'] }}"
    {% endif %}

cloud_init_hostname:
  file.managed:
    - name: /etc/cloud/cloud.cfg.d/stackdio_hostname.cfg
    - user: root
    - group: root
    - mode: 644
    - makedirs: true
    - contents:
      - "preserve_hostname: false"
      - "hostname: {{ grains['fqdn'] }}"
      - "fqdn: {{ grains['fqdn'] }}"

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

# Restart the appropriate service for this change to take effect
hostname-svc:
  service.running:
    - name: {{ hostname_service }}
    - watch:
      - cmd: set_hostname
      - file: stack_hostnames
      - file: hostname_file
