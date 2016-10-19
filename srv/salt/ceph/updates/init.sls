

include:
  - .{{ salt['pillar.get']('updates_init', 'default') }}
