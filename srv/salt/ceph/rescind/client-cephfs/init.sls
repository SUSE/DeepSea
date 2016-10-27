

include:
  - .{{ salt['pillar.get']('rescind_mds-client', 'default') }}
