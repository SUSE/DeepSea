include:
  - .{{ salt['pillar.get']('restart_mgr_force', 'default') }}
