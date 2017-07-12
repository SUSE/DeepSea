
include:
  - .{{ salt['pillar.get']('client-iscsi_init', 'default') }}
