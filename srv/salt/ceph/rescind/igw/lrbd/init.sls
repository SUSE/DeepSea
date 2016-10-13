

include:
  - .{{ salt['pillar.get']('rescind_igw_lrbd', 'default') }}
