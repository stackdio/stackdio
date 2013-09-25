{% set apache2 = salt['grains.filter_by']({
    'Debian': {
      'package': 'apache2',
      'service': 'apache2',
      'wwwroot': '/var/www',
    },
    'RedHat': {
      'package': 'httpd',
      'service': 'httpd',
      'wwwroot': '/var/www/html',
    }
}) %}

apache2:
  pkg:
    - installed
    - name: {{ apache2.package }}
  service:
    - running
    - name: {{ apache2.service }}
    - require:
      - pkg: apache2
