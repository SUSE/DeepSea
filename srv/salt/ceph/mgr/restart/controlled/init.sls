
include:
  - .{{ salt['pillar.get']('mgr_restart_controlled_init', 'default') }}

