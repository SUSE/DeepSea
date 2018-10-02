

include:
  - .{{ salt['pillar.get']('shutdown_init', 'default') }}
