

include:
  - .{{ salt['pillar.get']('restart_method', 'default') }}

