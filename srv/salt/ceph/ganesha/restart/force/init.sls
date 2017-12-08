
include:
  - .{{ salt['pillar.get']('ganesha_restart_force_init', 'default') }}

