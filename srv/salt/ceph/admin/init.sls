

include:
  - .begin
  - .{{ salt['pillar.get']('admin_method', 'default') }}
  - .complete
