
include:
  - .{{ salt['pillar.get']('terminate_ganesha', 'default') }}
