

include:
  - .{{ salt['pillar.get']('mds_auth', 'default') }}
