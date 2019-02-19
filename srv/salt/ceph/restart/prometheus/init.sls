include:
  - .{{ salt['pillar.get']('prometheus_restart_method', 'default') }}
