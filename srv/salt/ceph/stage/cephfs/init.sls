
include:
  - .{{ salt['pillar.get']('stage_cephfs', 'default') }}

