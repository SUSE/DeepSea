

include:
  - .{{ salt['pillar.get']('rescind_init', 'default') }}
