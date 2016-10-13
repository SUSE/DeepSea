

include:
  - .{{ salt['pillar.get']('remove_mon', 'default') }}
