
include:
  - .{{ salt['pillar.get']('terminate_rgw', 'default') }}
