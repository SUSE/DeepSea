include:
  - .{{ salt['pillar.get']('mon_restart_force_init', 'default') }}

