

include:
  - .begin
  - .keyring
  - .{{ salt['pillar.get']('osd_creation') }}
  - .complete

