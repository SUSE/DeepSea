
include:
  - .{{ salt['pillar.get']('igw_restart_reload_init', 'default') }}

