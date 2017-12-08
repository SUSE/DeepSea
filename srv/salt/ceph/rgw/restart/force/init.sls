
include:
  - .{{ salt['pillar.get']('rgw_restart_force_init', 'default') }}

