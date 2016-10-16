

include:
  - .{{ salt['pillar.get']('igw_config', 'default') }}
