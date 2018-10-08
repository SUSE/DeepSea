
include:
  - .{{ salt['pillar.get']('restart_osd_force', 'default') }}

