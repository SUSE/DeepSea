

include:
  - .{{ salt['pillar.get']('mds_pools', 'default') }}
