include:
  - .{{ salt['pillar.get']('mon_restart_method_lax', 'default') }}
