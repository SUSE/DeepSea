

include:
  - .{{ salt['pillar.get']('time_ntp', 'default') }}

