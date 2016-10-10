

include:
  - .{{ salt['pillar.get']('rescind_rgw-client', 'default') }}
