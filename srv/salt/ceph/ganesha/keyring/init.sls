

include:
  - .{{ salt['pillar.get']('ganesha_keyring', 'default') }}
