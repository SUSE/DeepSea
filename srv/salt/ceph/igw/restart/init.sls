
include:
  - .{{ salt['pillar.get']('igw_restart_init', 'default') }}

