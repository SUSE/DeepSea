

include:
  - .{{ salt['pillar.get']('mds_method', 'default') }}
