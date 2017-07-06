

include:
  - .{{ salt['pillar.get']('rescind_mgr', 'default') }}
