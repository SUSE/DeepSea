

include:
  - .begin
  - .{{ salt['pillar.get']('mon_method', 'default') }}
  - .complete
