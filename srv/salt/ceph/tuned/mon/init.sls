
include:
  - .{{ salt['pillar.get']('tuned_mon_init', 'default') }}
