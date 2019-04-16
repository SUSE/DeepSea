include:
  - .{{ salt['pillar.get']('monitoring_alertmanager_init', 'default') }}
