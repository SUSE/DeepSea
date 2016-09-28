

include:
  - .{{ salt['pillar.get']('updates_method', 'default') }}
