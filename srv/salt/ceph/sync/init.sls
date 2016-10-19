

include:
  - .{{ salt['pillar.get']('sync_init', 'default') }}
