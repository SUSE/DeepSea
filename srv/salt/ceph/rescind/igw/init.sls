

include:
  - .{{ salt['pillar.get']('rescind_igw', 'default') }}
