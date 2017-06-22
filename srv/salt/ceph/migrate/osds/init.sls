

include:
  - .{{ salt['pillar.get']('migrate_osds', 'default') }}
