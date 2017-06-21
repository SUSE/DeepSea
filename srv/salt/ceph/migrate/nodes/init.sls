

include:
  - .{{ salt['pillar.get']('migrate_nodes', 'default') }}
