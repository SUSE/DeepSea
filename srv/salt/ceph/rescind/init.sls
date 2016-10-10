

include:
  - .{{ salt['pillar.get']('rescind_method', 'default') }}
