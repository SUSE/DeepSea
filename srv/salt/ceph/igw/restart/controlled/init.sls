
include:
  - .{{ salt['pillar.get']('ganesha_restart_controlled_init', 'default') }}

