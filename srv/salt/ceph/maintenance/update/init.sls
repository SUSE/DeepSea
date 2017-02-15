

include:
  - .{{ salt['pillar.get']('maintenance_update_init', 'default') }}

