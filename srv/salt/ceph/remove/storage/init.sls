

include:
  - .{{ salt['pillar.get']('remove_storage', 'default') }}
