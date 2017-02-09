

include:
  - .{{ salt['pillar.get']('rescind_ganesha_keyring', 'default') }}
