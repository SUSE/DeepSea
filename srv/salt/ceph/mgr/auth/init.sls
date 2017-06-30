

include:
  - .{{ salt['pillar.get']('mgr_auth', 'default') }}
