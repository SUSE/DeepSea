include:
  - .{{ salt['pillar.get']('igw_restart_force_init', 'default') }}
