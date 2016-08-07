

include:
  - .keyring
  - .{{ salt['pillar.get']('osd_creation') }}

