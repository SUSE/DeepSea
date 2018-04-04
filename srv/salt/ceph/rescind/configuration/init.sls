
include:
  - .{{ salt['pillar.get']('rescind_configuration', 'default') }}
