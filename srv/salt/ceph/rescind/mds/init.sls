

include:
  - .{{ salt['pillar.get']('rescind_mds', 'default') }}
