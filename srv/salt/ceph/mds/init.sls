

include:
  - .begin
  - .{{ salt['pillar.get']('mds_method', 'default') }}
  - .complete
