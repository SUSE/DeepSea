
include:
  - .{{ salt['pillar.get']('osd_keyring_bootstrap', 'default') }}

