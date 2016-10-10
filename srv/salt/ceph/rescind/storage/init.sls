

include:
  - .{{ salt['pillar.get']('rescind_storage', 'default') }}
