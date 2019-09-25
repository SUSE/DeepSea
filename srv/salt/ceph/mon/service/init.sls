
include:
  - .{{ salt['pillar.get']('mon_service', 'default') }}
