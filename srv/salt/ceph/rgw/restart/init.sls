
include:
  - .{{ salt['pillar.get']('rgw_restart_init', 'default') }}

