

include:
  - .{{ salt['pillar.get']('configuration_create', 'default') }}
