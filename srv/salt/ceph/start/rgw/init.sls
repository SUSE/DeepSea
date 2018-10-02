
include:
  - .{{ salt['pillar.get']('start_rgw', 'default') }}
