

include:
  - .{{ salt['pillar.get']('osd_method', 'default') }}

