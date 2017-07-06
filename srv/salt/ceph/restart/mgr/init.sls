include:
  - .{{ salt['pillar.get']('mgr_restart_method', 'default') }}
