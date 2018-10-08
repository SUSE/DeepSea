include:
  - .{{ salt['pillar.get']('restart_ganesha_force', 'default') }}
