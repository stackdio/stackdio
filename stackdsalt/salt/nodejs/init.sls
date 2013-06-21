nodejs:
  pkg:
    - installed

npm:
  pkg:
    - installed
    - require:
      - pkg: nodejs
