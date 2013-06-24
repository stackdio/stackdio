base:
  '*':
    - core
  # All CDH4 roles pull from cdh4.init
  'roles:cdh4.*':
    - match: grain
    - cdh4
