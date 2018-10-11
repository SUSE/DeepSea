
include:
  - .{{ salt['pillar.get']('restart_igw_force', 'default') }}

