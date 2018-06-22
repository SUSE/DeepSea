
include:
  - .{{ salt['pillar.get']('tuned_mgr_init', 'default') }}
