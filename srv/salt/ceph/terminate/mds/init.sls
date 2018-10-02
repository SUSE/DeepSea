
include:
  - .{{ salt['pillar.get']('terminate_mds', 'default') }}
