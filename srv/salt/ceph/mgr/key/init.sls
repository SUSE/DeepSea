

include:
  - .{{ salt['pillar.get']('mgr_key', 'default') }}
