
include:
  - .{{ salt['pillar.get']('rescind_grafana', 'default') }}
