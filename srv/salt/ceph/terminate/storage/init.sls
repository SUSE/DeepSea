
include:
  - .{{ salt['pillar.get']('terminate_storage', 'default') }}
