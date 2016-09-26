

include:
  - .{{ salt['pillar.get']('osd_partition', 'default') }}

