

include:
  - .{{ salt['pillar.get']('startup_init', 'default') }}
