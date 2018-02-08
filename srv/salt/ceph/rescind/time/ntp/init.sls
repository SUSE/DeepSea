

include:
  - .{{ salt['pillar.get']('rescind_time_ntp', 'default') }}
