

include:
  - .{{ salt['pillar.get']('remove_storage_drain', 'default') }}
