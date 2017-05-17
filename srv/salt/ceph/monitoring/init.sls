

include:
  - .{{ salt['pillar.get']('monitoring_init', 'default') }}
