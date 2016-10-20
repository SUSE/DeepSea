

include:
  - .{{ salt['pillar.get']('rgw_init', 'default') }}
