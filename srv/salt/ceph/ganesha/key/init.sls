

include:
  - .{{ salt['pillar.get']('ganesha_key', 'default') }}
