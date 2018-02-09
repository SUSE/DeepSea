
include:
  - .{{ salt['pillar.get']('tuned_init', 'default') }}
