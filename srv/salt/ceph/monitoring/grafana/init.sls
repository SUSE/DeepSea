
include:
  - .{{ salt['pillar.get']('monitoring_grafana', 'disabled') }}
