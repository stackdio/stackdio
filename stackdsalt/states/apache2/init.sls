apache2:
  pkg:
    - installed
  service:
    - running
    - require:
      - pkg: apache2
      - file: /var/www/index.html

/var/www/index.html:
  file:
    - managed
    - source: salt://apache2/index.html
    - require:
      - pkg: apache2
