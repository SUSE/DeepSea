
include:
  - .{{ salt['pillar.get']('openattic_restart_controlled_init', 'default') }}

