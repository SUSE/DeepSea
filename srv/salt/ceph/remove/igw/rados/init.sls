

include:
  - .{{ salt['pillar.get']('remove_igw_rados', 'default') }}
