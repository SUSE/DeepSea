
include:
  - .{{ salt['pillar.get']('tuned_osd_init', 'default') }}
