

include:
  - .{{ salt['pillar.get']('rescind_rgw-nfs', 'default') }}
