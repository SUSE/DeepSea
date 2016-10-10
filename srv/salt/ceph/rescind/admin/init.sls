

include:
  - .{{ salt['pillar.get']('rescind_admin', 'default') }}
