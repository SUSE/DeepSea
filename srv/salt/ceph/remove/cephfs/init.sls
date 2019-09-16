

include:
  - .{{ salt['pillar.get']('remove_mds', 'default') }}
