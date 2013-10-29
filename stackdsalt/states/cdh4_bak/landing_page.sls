{% from 'apache2/init.sls' import apache2 with context %}

{% if salt['pillar.get']('cdh4:landing_page', False) %}
# Install apache
include:
  - apache2

# Setup the landing page
{{ apache2.wwwroot }}/index.html:
  file:
    - managed
    - source: salt://cdh4/files/landing_page.html
    - user: root
    - group: root
    - mode: 755
    - template: jinja
    - require:
      - pkg: {{ apache2.package }}
{% endif %}
