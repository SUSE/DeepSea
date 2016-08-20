

include:
  - .begin
  - .{{ salt['pillar.get']('update_method', 'default') }}
  - .complete
