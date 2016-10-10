

include:
  - .{{ salt['pillar.get']('rescind_mon', 'default') }}
