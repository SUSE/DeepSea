

include:
  - .{{ salt['pillar.get']('configuration_init', 'default') }}
