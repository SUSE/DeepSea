

include:
  - .{{ salt['pillar.get']('ganesha_init', 'default') }}
