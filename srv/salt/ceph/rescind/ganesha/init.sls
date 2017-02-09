

include:
  - .{{ salt['pillar.get']('rescind_rgw', 'default') }}
