

include:
  - .{{ salt['pillar.get']('mon_init', 'default') }}
