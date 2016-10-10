

include:
  - .{{ salt['pillar.get']('purge_storage', 'default') }}
