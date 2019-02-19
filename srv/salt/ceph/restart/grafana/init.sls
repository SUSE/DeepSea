include:
  - .{{ salt['pillar.get']('grafana_restart_method', 'default') }}
