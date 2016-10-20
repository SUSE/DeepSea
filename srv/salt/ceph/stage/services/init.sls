
include:
  - .{{ salt['pillar.get']('stage_services', 'default') }}

