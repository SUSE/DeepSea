

include:
  - .{{ salt['pillar.get']('rescind_rbd-client', 'default') }}
