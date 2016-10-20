

include:
  - .{{ salt['pillar.get']('osd_init', 'default') }}

