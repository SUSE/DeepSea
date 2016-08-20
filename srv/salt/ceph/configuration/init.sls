

include:
  - .begin
  - .{{ salt['pillar.get']('configuration_method', 'default') }}
  - .complete
