

include:
  - .begin
  - .{{ salt['pillar.get']('configure_method', 'default') }}
  - .complete
