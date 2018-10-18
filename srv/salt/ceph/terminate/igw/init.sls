
include:
  - .{{ salt['pillar.get']('terminate_igw', 'default') }}
