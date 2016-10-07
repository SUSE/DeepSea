
include:
  - .{{ salt['pillar.get']('benchmark_cephfs_method', 'default') }}

