

include:
  - .begin
  - .{{ salt['pillar.get']('rgw_method', 'default') }}
  - .complete
