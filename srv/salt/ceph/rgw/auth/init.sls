

include:
  - .{{ salt['pillar.get']('rgw_auth', 'default') }}
