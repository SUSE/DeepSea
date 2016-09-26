

include:
  - .{{ salt['pillar.get']('mds_keyring', 'default') }}
