

include:
  - .{{ salt['pillar.get']('mon_method', 'default') }}
