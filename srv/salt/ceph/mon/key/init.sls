

include:
  - .{{ salt['pillar.get']('mon_key', 'default') }}
