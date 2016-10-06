

include:
  - .{{ salt['pillar.get']('updates_restart', 'default') }}
