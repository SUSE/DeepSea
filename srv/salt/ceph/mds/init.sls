

include:
  - .{{ salt['pillar.get']('mds_init', 'default') }}
