

include:
  - .{{ salt['pillar.get']('rescind_client-nfs', 'default') }}
