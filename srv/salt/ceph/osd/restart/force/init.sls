
include:
  - .{{ salt['pillar.get']('osd_restart_force_init', 'default') }}

