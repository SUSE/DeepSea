

include:
  - .{{ salt['pillar.get']('rgw_keyring', 'default') }}
