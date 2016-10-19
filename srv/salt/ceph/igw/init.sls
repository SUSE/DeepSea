

include:
  - .{{ salt['pillar.get']('igw_init', 'default') }}
