

include:
  - .{{ salt['pillar.get']('igw_method', 'default') }}
