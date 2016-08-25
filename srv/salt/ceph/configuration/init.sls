

include:
  - .{{ salt['pillar.get']('configuration_method', 'default') }}
