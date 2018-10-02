
include:
  - .{{ salt['pillar.get']('terminate_mon', 'default') }}
