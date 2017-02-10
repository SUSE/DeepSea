

include:
  - .{{ salt['pillar.get']('ganesha_service', 'default') }}