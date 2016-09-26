

include:
  - .{{ salt['pillar.get']('osd_scheduler', 'default') }}

