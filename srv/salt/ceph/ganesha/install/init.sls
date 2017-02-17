

include:
  - .{{ salt['pillar.get']('ganesha_install', 'default') }}