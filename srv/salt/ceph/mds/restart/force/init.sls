
include:
  - .{{ salt['pillar.get']('mds_restart_force_init', 'default') }}

