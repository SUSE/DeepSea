

include:
  - .{{ salt['pillar.get']('ganesha_auth_del', 'default') }}
