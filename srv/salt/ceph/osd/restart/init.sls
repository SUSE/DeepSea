
include:
  - .{{ salt['pillar.get']('osd_restart_init', 'default') }}

