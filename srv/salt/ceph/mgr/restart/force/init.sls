
include:
  - .{{ salt['pillar.get']('mgr_restart_force_init', 'default') }}

