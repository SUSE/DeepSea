
include:
  - .{{ salt['pillar.get']('stage_nfs-ganesha', 'default') }}