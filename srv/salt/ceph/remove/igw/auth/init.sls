

include:
  - .{{ salt['pillar.get']('remove_igw_auth', 'default') }}
