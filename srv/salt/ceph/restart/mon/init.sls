include:
  - .{{ salt['pillar.get']('mon_restart_method', 'default') }}
