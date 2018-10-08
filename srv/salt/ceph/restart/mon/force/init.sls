include:
  - .{{ salt['pillar.get']('restart_mon_force', 'default') }}
