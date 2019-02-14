
include:
  - .{{ salt['pillar.get']('rescind_prometheus', 'default') }}
