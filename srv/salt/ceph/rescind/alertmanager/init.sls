
include:
  - .{{ salt['pillar.get']('rescind_alertmanager', 'default') }}
