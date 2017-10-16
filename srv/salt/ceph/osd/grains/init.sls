

include:
  - .{{ salt['pillar.get']('osd_grains', 'default') }}

