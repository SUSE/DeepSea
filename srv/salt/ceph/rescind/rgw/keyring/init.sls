

include:
  - .{{ salt['pillar.get']('rescind_rgw_keyring', 'default') }}
