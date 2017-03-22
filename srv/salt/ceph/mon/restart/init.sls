
include:
  - .{{ salt['pillar.get']('mon_restart_init', 'default') }}

