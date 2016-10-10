

include:
  - .{{ salt['pillar.get']('rescind_mds-nfs', 'default') }}
