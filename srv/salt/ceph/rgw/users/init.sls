

include:
  - .{{ salt['pillar.get']('rgw_users', 'default') }}
