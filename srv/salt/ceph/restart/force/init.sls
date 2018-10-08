include:
  - .{{ salt['pillar.get']('restart_force', 'default') }}
