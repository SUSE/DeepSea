

include:
  - .{{ salt['pillar.get']('rescind_igw_keyring', 'default') }}
