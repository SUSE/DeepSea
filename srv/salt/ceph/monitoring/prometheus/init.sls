
include:
  - .{{ salt['pillar.get']('prometheus_init', 'default') }}
