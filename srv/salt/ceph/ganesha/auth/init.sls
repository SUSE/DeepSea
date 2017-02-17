

include:
  - .{{ salt['pillar.get']('ganesha_auth', 'default') }}
