

include:
  - .{{ salt['pillar.get']('rescind_ganesha', 'default') }}
