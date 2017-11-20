
include:
  - .{{ salt['pillar.get']('osd_restart_controlled_init', 'default') }}

