

include:
  - .{{ salt['pillar.get']('rescind_storage_terminate', 'default') }}
