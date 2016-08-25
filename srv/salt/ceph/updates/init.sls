

include:
  - .{{ salt['pillar.get']('update_method', 'default') }}
