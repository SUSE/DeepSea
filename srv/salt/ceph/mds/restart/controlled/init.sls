
include:
  - .{{ salt['pillar.get']('mds_restart_controlled_init', 'default') }}

