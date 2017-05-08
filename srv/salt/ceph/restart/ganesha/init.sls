include:
  - .{{ salt['pillar.get']('ganesha_restart_method', 'default') }}
