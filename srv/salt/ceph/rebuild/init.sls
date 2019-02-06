

include:
  - .{{ salt['pillar.get']('rebuild_init', 'default') }}
