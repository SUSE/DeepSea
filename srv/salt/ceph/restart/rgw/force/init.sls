
include:
  - .{{ salt['pillar.get']('restart_rgw_force', 'default') }}
