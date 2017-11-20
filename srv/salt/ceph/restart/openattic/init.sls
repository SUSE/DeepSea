include:
  - .{{ salt['pillar.get']('openattic_restart_method', 'default') }}
