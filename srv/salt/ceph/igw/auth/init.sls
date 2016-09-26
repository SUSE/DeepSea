

include:
  - .{{ salt['pillar.get']('igw_auth', 'default') }}
