

include:
  - .{{ salt['pillar.get']('ganesha_configure', 'default') }}