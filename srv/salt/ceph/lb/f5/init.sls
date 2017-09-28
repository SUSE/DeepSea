

include:
  - .{{ salt['pillar.get']('lb_f5', 'default') }}
