

include:
  - .{{ salt['pillar.get']('openattic_keyring', 'default') }}
