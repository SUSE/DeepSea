

include:
  - .{{ salt['pillar.get']('mgr_init', 'default') }}
