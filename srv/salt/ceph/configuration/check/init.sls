

include:
  - .{{ salt['pillar.get']('configuration_check', 'default') }}
