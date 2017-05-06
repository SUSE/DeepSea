
include:
  - .{{ salt['pillar.get']('rescind_openattic_keyring', 'default') }}
