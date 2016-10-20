

include:
  - .{{ salt['pillar.get']('refresh_init', 'default') }}
