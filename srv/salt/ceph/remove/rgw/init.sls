

include:
  - .{{ salt['pillar.get']('remove_rgw', 'default') }}
