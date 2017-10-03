
include:
  - .{{ salt['pillar.get']('migrate_subvolume', 'default') }}
