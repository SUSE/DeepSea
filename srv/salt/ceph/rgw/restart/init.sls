
include:
  - .{{ salt['pillar.get']('restart', 'default') }}

