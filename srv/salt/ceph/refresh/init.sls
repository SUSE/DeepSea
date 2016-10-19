

include:
  - .{{ salt['pillar.get']('refresh_method', 'default') }}
