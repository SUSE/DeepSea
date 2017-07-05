
include:
  - .{{ salt['pillar.get']('migrate_policy', 'default') }}
