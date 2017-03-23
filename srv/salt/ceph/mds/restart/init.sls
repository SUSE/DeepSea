
include:
  - .{{ salt['pillar.get']('mds_restart_init', 'default') }}

