
include:
  - .{{ salt['pillar.get']('ganesha_restart_init', 'default') }}

