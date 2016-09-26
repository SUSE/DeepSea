

include:
  - .{{ salt['pillar.get']('osd_keyring', 'default') }}

