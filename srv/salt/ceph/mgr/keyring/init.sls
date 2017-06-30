

include:
  - .{{ salt['pillar.get']('mgr_keyring', 'default') }}
