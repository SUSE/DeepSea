include:
  - .{{ salt['pillar.get']('mds_restart_method_lax', 'default') }}
