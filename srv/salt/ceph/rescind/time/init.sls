
include:
  - .{{ salt['pillar.get']('rescind_time', 'default') }}
