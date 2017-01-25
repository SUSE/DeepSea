

include:
  - .{{ salt['pillar.get']('purge_init', 'default') }}
