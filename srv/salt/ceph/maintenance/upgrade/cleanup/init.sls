include:
  - .{{ salt['pillar.get']('maintenance_upgrade_cleanup', 'default') }}
