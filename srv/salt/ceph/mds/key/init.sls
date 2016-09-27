

include:
  - .{{ salt['pillar.get']('mds_key', 'default') }}
