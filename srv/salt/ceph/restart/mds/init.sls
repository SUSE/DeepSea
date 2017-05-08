include:
  - .{{ salt['pillar.get']('mds_restart_method', 'default') }}
