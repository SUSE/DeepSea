include:
  - .{{ salt['pillar.get']('rgw_restart_method', 'default') }}
