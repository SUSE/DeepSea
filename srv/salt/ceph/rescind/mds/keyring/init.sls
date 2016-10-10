

include:
  - .{{ salt['pillar.get']('rescind_mds_keyring', 'default') }}
