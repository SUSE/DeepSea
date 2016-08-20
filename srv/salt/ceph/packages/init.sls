

include:
  - .begin
  - .{{ salt['pillar.get']('package_method', 'default') }}
  - .complete
