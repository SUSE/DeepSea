
include:
  - .{{ salt['pillar.get']('start_storage', 'default') }}
