

include:
  - .{{ salt['pillar.get']('rescind_master', 'default') }}
