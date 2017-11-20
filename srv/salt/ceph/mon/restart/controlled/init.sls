include:
  - .{{ salt['pillar.get']('mon_restart_controlled_init', 'default') }}

