

include:
  - .{{ salt['pillar.get']('rgw_key', 'default') }}
