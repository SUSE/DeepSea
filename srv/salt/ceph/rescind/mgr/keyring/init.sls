

include:
  - .{{ salt['pillar.get']('rescind_mgr_keyring', 'default') }}
