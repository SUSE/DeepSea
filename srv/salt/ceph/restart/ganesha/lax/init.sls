include:
  - .{{ salt['pillar.get']('ganesha_restart_method_lax', 'default') }}
