
include:
  - .{{ salt['pillar.get']('pool_method', 'default') }}
