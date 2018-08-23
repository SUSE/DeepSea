

include:
  - .{{ salt['pillar.get']('remove_migrated', 'default') }}
