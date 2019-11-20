
include:
  - .{{ salt['pillar.get']('rescind_crash', 'default') }}
