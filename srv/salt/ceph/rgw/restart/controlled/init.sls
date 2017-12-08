
include:
  - .{{ salt['pillar.get']('rgw_restart_controlled_init', 'default') }}

