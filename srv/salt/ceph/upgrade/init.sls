

include:
  - .{{ salt['pillar.get']('upgrade_init', 'default') }}
