

include:
  - .{{ salt['pillar.get']('sync_method', 'default') }}
