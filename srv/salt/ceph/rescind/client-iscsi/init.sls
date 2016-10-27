

include:
  - .{{ salt['pillar.get']('rescind_igw-client', 'default') }}
