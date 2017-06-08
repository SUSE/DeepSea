

include:
  - .{{ salt['pillar.get']('ganesha_config', 'default') }}