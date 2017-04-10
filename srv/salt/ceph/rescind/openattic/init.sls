

include:
  - .{{ salt['pillar.get']('rescind_openattic', 'default') }}
