

include:
  - .{{ salt['pillar.get']('rgw_method', 'default') }}
