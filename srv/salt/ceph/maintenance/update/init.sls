

include:
  - .{{ salt['pillar.get']('maintenance_method', 'default') }}

