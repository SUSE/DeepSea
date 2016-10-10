

include:
  - .{{ salt['pillar.get']('rescind_igw_auth', 'default') }}
