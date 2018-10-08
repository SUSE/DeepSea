include:
  - .{{ salt['pillar.get']('restart_mds_force', 'default') }}
