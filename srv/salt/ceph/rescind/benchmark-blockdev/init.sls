

include:
  - .{{ salt['pillar.get']('rescind_benchmark-blockdev', 'default') }}
