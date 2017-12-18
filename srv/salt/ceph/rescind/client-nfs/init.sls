

include:
  - .{{ salt['pillar.get']('rescind_client-ganesha', 'default') }}
